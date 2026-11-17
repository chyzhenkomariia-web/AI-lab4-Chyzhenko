"""Спільний модуль для всіх завдань лабораторної роботи №4.

send_prompt() надсилає запит до Gemini API (з роллю, temperature, top-p,
за потреби з режимом JSON) і зберігає prompt та відповідь у results/<task>.json.

Економія квоти: якщо запит із таким самим title вже є в results/<task>.json,
він НЕ надсилається повторно, а повертається збережена відповідь. Тому після
помилки чи вичерпання ліміту достатньо просто запустити скрипт ще раз.
Щоб виконати запит заново, видаліть відповідний файл у папці results/.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

BASE = Path(__file__).parent
RESULTS = BASE / "results"
RESULTS.mkdir(exist_ok=True)
DATA = BASE / "data"

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("Не знайдено GEMINI_API_KEY. Створіть файл .env за зразком .env.example")

client = genai.Client(api_key=api_key)


def read_text(name):
    """Читає текстовий файл із папки data/."""
    return (DATA / name).read_text(encoding="utf-8").strip()


def load_records(task):
    path = RESULTS / f"{task}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save_json(name, data):
    """Зберігає допоміжні дані (перевірки, статистику) у results/<name>.json."""
    (RESULTS / f"{name}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def send_prompt(task, title, prompt, system=None, temperature=0.0, top_p=None,
                json_mode=False, reuse=True, retries=4):
    """Надсилає prompt моделі й повертає текст відповіді.

    task        -- назва файлу з результатами (наприклад, "task1")
    title       -- підпис запиту у звіті (унікальний у межах task)
    system      -- системна інструкція (роль моделі) або None
    temperature -- випадковість генерації
    top_p       -- nucleus sampling (None = значення моделі за замовчуванням)
    json_mode   -- True: модель зобов'язана повернути чистий JSON
    reuse       -- True: якщо відповідь уже збережено, запит не надсилається
    """
    records = load_records(task)
    if reuse:
        for r in records:
            if r["title"] == title and r.get("answer"):
                print(f"-> {title}: вже є, пропускаю")
                return r["answer"]

    config = types.GenerateContentConfig(
        system_instruction=system,
        temperature=temperature,
        top_p=top_p,
        response_mime_type="application/json" if json_mode else None,
    )

    print(f"-> {title}")
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL, contents=prompt, config=config)
            if not response.text:
                raise RuntimeError("порожня відповідь")
            break
        except Exception as error:
            text = str(error)
            if "PerDay" in text or "per day" in text.lower():
                raise SystemExit(
                    "\nВичерпано ДОБОВИЙ ліміт запитів для моделі " + MODEL + ".\n"
                    "Виконані запити збережено. Або запустіть скрипт пізніше,\n"
                    "або змініть GEMINI_MODEL у файлі .env на іншу модель і запустіть знову.")
            wait = 20 * attempt
            print(f"   помилка ({error.__class__.__name__}: {text[:120]}), повтор через {wait} с")
            time.sleep(wait)
    else:
        raise SystemExit(f"Запит «{title}» не вдався після {retries} спроб")

    record = {
        "title": title,
        "model": response.model_version or MODEL,
        "temperature": temperature,
        "top_p": top_p,
        "json_mode": json_mode,
        "system": system,
        "prompt": prompt,
        "answer": response.text,
        "words": len(response.text.split()),
        "time": datetime.now().isoformat(timespec="seconds"),
    }
    records = [r for r in records if r["title"] != title]
    records.append(record)
    save_json(task, records)

    print(f"   отримано відповідь: {record['words']} слів\n")
    time.sleep(6)  # пауза, щоб не перевищити ліміт запитів за хвилину
    return response.text


if __name__ == "__main__":
    print(send_prompt("check", "Перевірка", "Скажи одним реченням, яка ти модель.", reuse=False))
