"""Збирає всі результати з папки results/ в один файл results.md."""
import json
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
TITLES = {
    "task1": "Завдання 1. Звичайний і просунутий prompt",
    "task2": "Завдання 2. Декомпозиція",
    "task3": "Завдання 3. Імітація ReAct",
    "task4": "Завдання 4. Структурований результат (JSON)",
    "task5": "Завдання 5. Великий контекст і chunking",
    "task6": "Завдання 6. Temperature і top-p",
}
EXTRA = {"task4": "task4_check", "task5": "task5_stats", "task6": "task6_metrics"}

parts = ["# Результати запитів до LLM (лабораторна робота №4)\n"]
for task, heading in TITLES.items():
    path = RESULTS / f"{task}.json"
    if not path.exists():
        continue
    parts.append(f"\n## {heading}\n")
    for r in json.loads(path.read_text(encoding="utf-8")):
        parts.append(f"\n### {r['title']}\n")
        parts.append(f"*Модель: {r['model']}, temperature = {r['temperature']}, "
                     f"top_p = {r['top_p']}, JSON-режим: {r['json_mode']}, "
                     f"обсяг: {r['words']} слів*\n")
        if r["system"]:
            parts.append(f"**System:** {r['system']}\n")
        prompt = r["prompt"] if len(r["prompt"]) < 4000 else r["prompt"][:4000] + "\n...[скорочено]"
        parts.append(f"**Prompt:**\n\n```\n{prompt}\n```\n")
        parts.append(f"**Відповідь:**\n\n{r['answer']}\n")
    extra = RESULTS / f"{EXTRA.get(task, '')}.json"
    if task in EXTRA and extra.exists():
        parts.append(f"\n**Автоматична перевірка ({extra.name}):**\n\n```json\n"
                     + extra.read_text(encoding="utf-8") + "\n```\n")

(Path(__file__).parent / "results.md").write_text("\n".join(parts), encoding="utf-8")
print("Створено results.md")
