"""Завдання 5. Робота з великим контекстом.

Документ: стаття «Attention Is All You Need» (Vaswani et al., 2017), data/long_text.txt.

5.1  Увесь текст одним запитом.
5.2  Chunking (Map-Reduce): текст ділиться на фрагменти по межах абзаців,
     кожен фрагмент узагальнюється окремо (map), потім часткові
     узагальнення об'єднуються в одне (reduce).
5.3  Порівняння: окрім ручної оцінки, Python автоматично перевіряє, які
     ключові факти статті (числа й терміни) потрапили в кожне узагальнення.
*    Додатково: sliding window (фрагменти з перекриттям):
     python task5.py window
"""
import sys

from llm_client import send_prompt, read_text, save_json

TASK = "task5"
CHUNK_SIZE = 9000   # символів у фрагменті
OVERLAP = 1500      # перекриття для sliding window

text = read_text("long_text.txt")

SYSTEM = ("Ти викладач курсу «Основи штучного інтелекту». Працюй лише з наданим "
          "текстом, нічого не вигадуй. Відповідай українською, терміни можна "
          "дублювати англійською в дужках.")

FINAL_TASK = ("Склади узагальнення наукової статті для студентів:\n"
              "1) проблема, яку розв'язують автори;\n"
              "2) архітектура запропонованої моделі (основні складові);\n"
              "3) 7-10 ключових ідей;\n"
              "4) результати експериментів із конкретними числами;\n"
              "5) висновок (2-3 речення).\n"
              "Структуруй відповідь заголовками.")

# Контрольний список фактів статті
FACTS = [
    ("BLEU 28.4 (EN-DE)", ["28.4", "28,4"]),
    ("BLEU 41.8 (EN-FR)", ["41.8", "41,8"]),
    ("6 шарів енкодера/декодера", ["6 шар", "шість шар", "n = 6", "n=6", "6 ідентичн", "6 однаков"]),
    ("8 голів уваги", ["8 гол", "вісім гол", "h = 8", "h=8", "8 паралельн"]),
    ("d_model = 512", ["512"]),
    ("d_ff = 2048", ["2048", "2 048"]),
    ("dropout 0.1", ["dropout", "дропаут", "відсіюван"]),
    ("label smoothing", ["label smoothing", "згладжування міток", "згладжування міт"]),
    ("оптимізатор Adam", ["adam"]),
    ("warmup 4000 кроків", ["4000", "4 000"]),
    ("8 GPU P100", ["p100", "8 gpu", "вісім gpu", "8 графічн"]),
    ("3.5 дні навчання (big)", ["3.5 д", "3,5 д"]),
    ("12 годин навчання (base)", ["12 год"]),
    ("позиційне кодування", ["позиційн"]),
    ("масштабований скалярний добуток", ["scaled dot", "масштабован"]),
    ("синтаксичний розбір англійської", ["constituency", "синтаксичн", "парсинг", "розбор", "розбір"]),
]


def check_facts(answer):
    low = answer.lower().replace(" ", " ")
    found = [name for name, variants in FACTS if any(v in low for v in variants)]
    missing = [name for name, _ in FACTS if name not in found]
    return {"found": len(found), "total": len(FACTS), "missing": missing}


def make_chunks(text, size, overlap=0):
    """Ділить текст на фрагменти до size символів, не розриваючи рядки.
    overlap > 0 (sliding window): наступний фрагмент починається з останніх
    рядків попереднього загальним обсягом до overlap символів."""
    lines = [l for l in text.splitlines() if l.strip()]
    chunks, current = [], []
    for line in lines:
        if current and sum(len(l) + 1 for l in current) + len(line) > size:
            chunks.append("\n".join(current))
            tail, total = [], 0
            for l in reversed(current):          # беремо кінець попереднього фрагмента
                if total + len(l) > overlap:
                    break
                tail.insert(0, l)
                total += len(l) + 1
            current = tail
        current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


def map_reduce(chunks, tag):
    summaries = []
    for i, chunk in enumerate(chunks, 1):
        s = send_prompt(TASK, f"{tag}. Фрагмент {i}/{len(chunks)}",
            f"Це фрагмент {i} із {len(chunks)} наукової статті. Узагальни його "
            "у 4-6 реченнях. Обов'язково збережи всі числа, назви методів і "
            f"терміни, що є у фрагменті.\n\nФрагмент:\n{chunk}",
            system=SYSTEM)
        summaries.append(f"[Фрагмент {i}]\n{s}")
    return send_prompt(TASK, f"{tag}. Загальне узагальнення",
        "Нижче наведено узагальнення послідовних фрагментів однієї статті. "
        f"{FINAL_TASK}\n\nУзагальнення фрагментів:\n" + "\n\n".join(summaries),
        system=SYSTEM)


stats = {"chars": len(text), "words": len(text.split()), "chunk_size": CHUNK_SIZE}

# Без chunking
full = send_prompt(TASK, "5.1 Без chunking", f"{FINAL_TASK}\n\nСтаття:\n{text}", system=SYSTEM)
stats["no_chunking"] = {"requests": 1, "words": len(full.split()), "facts": check_facts(full)}

# Chunking
chunks = make_chunks(text, CHUNK_SIZE)
chunked = map_reduce(chunks, "5.2 Chunking")
stats["chunking"] = {"requests": len(chunks) + 1, "chunk_lengths": [len(c) for c in chunks],
                     "words": len(chunked.split()), "facts": check_facts(chunked)}

# sliding window
if "window" in sys.argv:
    windows = make_chunks(text, CHUNK_SIZE, OVERLAP)
    windowed = map_reduce(windows, "5.4 Sliding window")
    stats["sliding_window"] = {"requests": len(windows) + 1, "overlap": OVERLAP,
                               "chunk_lengths": [len(c) for c in windows],
                               "words": len(windowed.split()), "facts": check_facts(windowed)}

save_json("task5_stats", stats)
print("\n=== Порівняння ===")
for key in ("no_chunking", "chunking", "sliding_window"):
    if key in stats:
        s = stats[key]
        print(f"{key}: запитів {s['requests']}, слів {s['words']}, "
              f"фактів {s['facts']['found']}/{s['facts']['total']}, пропущено: {s['facts']['missing']}")
