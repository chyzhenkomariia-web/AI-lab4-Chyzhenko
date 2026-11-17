"""Завдання 6. Вплив temperature і top-p на генерацію.

Задача: згенерувати 5 ідей навчальних проєктів з машинного навчання.
Кожне налаштування запускається RUNS разів, щоб оцінити стабільність.

Метрики, що рахуються автоматично:
- similarity  -- схожість відповідей між прогонами (difflib, 1 = однакові);
- unique_ratio -- частка унікальних слів (лексичне різноманіття);
- words       -- середня довжина відповіді.
"""
from difflib import SequenceMatcher
from itertools import combinations

from llm_client import send_prompt, save_json

TASK = "task6"
RUNS = 2

PROMPT = ("Запропонуй 5 ідей навчальних проєктів з машинного навчання для студентів "
          "2 курсу. Для кожної ідеї вкажи назву і одне речення з описом. Без вступу.")


def similarity(answers):
    pairs = list(combinations(answers, 2))
    return round(sum(SequenceMatcher(None, a.split(), b.split(), autojunk=False).ratio() for a, b in pairs) / len(pairs), 3)


def unique_ratio(answer):
    words = answer.lower().split()
    return round(len(set(words)) / len(words), 3)


def experiment(group, value, temperature, top_p=None):
    answers = [send_prompt(TASK, f"{group} = {value} | прогін {r}", PROMPT,
                           temperature=temperature, top_p=top_p)
               for r in range(1, RUNS + 1)]
    return {
        "group": group, "value": value, "temperature": temperature, "top_p": top_p,
        "similarity": similarity(answers),
        "unique_ratio": round(sum(map(unique_ratio, answers)) / RUNS, 3),
        "words": round(sum(len(a.split()) for a in answers) / RUNS, 1),
    }


metrics = []
for t in (0, 0.5, 1):
    metrics.append(experiment("temperature", t, temperature=t))
for p in (0.5, 0.8, 1.0):
    metrics.append(experiment("top_p", p, temperature=1.0, top_p=p))

save_json("task6_metrics", metrics)
print("\nПараметр        | схожість прогонів | різноманіття слів | слів")
for m in metrics:
    print(f"{m['group']:>11} = {m['value']:<3} | {m['similarity']:^17} | {m['unique_ratio']:^17} | {m['words']}")
