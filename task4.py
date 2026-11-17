"""Завдання 4. Структурований результат (JSON) і його перевірка засобами Python.

1. Модель отримує інструкцію повернути JSON заданої структури (режим JSON у API).
2. Python розбирає відповідь (json.loads) і перевіряє структуру: ключі, типи,
   кількість елементів, порожні значення.
3. Якщо перевірка не пройдена, модель отримує список помилок і виправляє JSON
   (один повторний запит: цикл «згенерувати -> перевірити -> виправити»).
"""
import json
import re

from llm_client import send_prompt, read_text, save_json

TASK = "task4"
text = read_text("short_text.txt")

SCHEMA = {
    "topic": str,
    "key_ideas": list,
    "keywords": list,
    "facts": list,
    "author_opinions": list,
    "conclusion": str,
}
LIMITS = {"key_ideas": (3, 5), "keywords": (5, 8), "facts": (2, 6), "author_opinions": (1, 4)}

prompt = f"""Проаналізуй текст і поверни результат ТІЛЬКИ у форматі JSON такої структури:
{{
  "topic": "тема одним реченням",
  "key_ideas": ["3-5 ключових ідей"],
  "keywords": ["5-8 ключових слів або термінів"],
  "facts": ["2-6 фактичних тверджень з тексту"],
  "author_opinions": ["1-4 висновки або оцінки автора"],
  "conclusion": "висновок до 2 речень"
}}
Мова значень: українська. Жодного тексту поза JSON.

Текст:
{text}"""


def validate(raw):
    """Повертає (розібраний JSON або None, список помилок)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())  # на випадок ```json
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, [f"некоректний JSON: {e}"]
    if not isinstance(data, dict):
        return None, ["корінь JSON має бути об'єктом"]

    errors = []
    for key, typ in SCHEMA.items():
        if key not in data:
            errors.append(f"відсутній ключ '{key}'")
        elif not isinstance(data[key], typ):
            errors.append(f"'{key}' має тип {type(data[key]).__name__}, очікувався {typ.__name__}")
        elif not data[key]:
            errors.append(f"'{key}' порожній")
    for key, (lo, hi) in LIMITS.items():
        if isinstance(data.get(key), list):
            n = len(data[key])
            if not lo <= n <= hi:
                errors.append(f"'{key}': {n} елементів, а має бути {lo}-{hi}")
            if not all(isinstance(x, str) and x.strip() for x in data[key]):
                errors.append(f"'{key}': усі елементи мають бути непорожніми рядками")
    extra = set(data) - set(SCHEMA)
    if extra:
        errors.append(f"зайві ключі: {sorted(extra)}")
    return data, errors


raw = send_prompt(TASK, "1. Генерація JSON", prompt, json_mode=True)
data, errors = validate(raw)
attempts = [{"step": "1. Генерація JSON", "errors": errors}]

if errors:
    print("Знайдено помилки структури:", errors)
    raw = send_prompt(TASK, "2. Виправлення JSON",
        "Твій JSON не пройшов перевірку. Помилки:\n- " + "\n- ".join(errors) +
        f"\n\nВиправ їх і поверни тільки JSON.\n\nПопередня відповідь:\n{raw}\n\n{prompt}",
        json_mode=True)
    data, errors = validate(raw)
    attempts.append({"step": "2. Виправлення JSON", "errors": errors})

result = {"structure_ok": not errors, "attempts": attempts, "parsed": data}
save_json("task4_check", result)

print("\nСтруктура коректна:" if not errors else "\nСтруктура НЕкоректна:", errors or "")
if data:
    # Демонстрація роботи з розібраними даними як зі звичайним словником Python
    print("Тема:", data.get("topic"))
    for i, idea in enumerate(data.get("key_ideas", []), 1):
        print(f"  ідея {i}: {idea}")
    print("Ключові слова:", ", ".join(data.get("keywords", [])))
    print(f"Фактів: {len(data.get('facts', []))}, думок автора: {len(data.get('author_opinions', []))}")
