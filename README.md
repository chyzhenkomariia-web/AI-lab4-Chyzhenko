# Лабораторна робота №4. Просунутий Prompt Engineering, Context Engineering та керування генерацією

Модель: Google Gemini (бібліотека `google-genai`). Предметна область: штучний інтелект.

## Структура

| Файл | Призначення |
|---|---|
| `llm_client.py` | `send_prompt()`: запит до Gemini (роль, temperature, top-p, JSON-режим), збереження в `results/<task>.json`; вже виконані запити не повторюються |
| `data/short_text.txt` | короткий текст про галюцинації LLM (завдання 1-4) |
| `pdf_to_txt.py` | витягує текст статті з PDF у `data/long_text.txt` |
| `task1.py` | звичайний і просунутий prompt |
| `task2.py` | декомпозиція (ланцюжок із 4 prompt) проти одного prompt |
| `task3.py` | імітація ReAct (план → Думка/Дія/Спостереження → перевірка → результат) |
| `task4.py` | JSON-результат, перевірка структури в Python, автоматичне виправлення |
| `task5.py` | великий документ: без chunking, chunking (Map-Reduce), sliding window, автоматична перевірка фактів |
| `task6.py` | temperature 0 / 0.5 / 1 і top-p 0.5 / 0.8 / 1.0, метрики стабільності й різноманіття |
| `make_report.py` | збирає всі результати в `results.md` |

## Запуск

```bash
pip install -r requirements.txt
python pdf_to_txt.py attention.pdf      # стаття arXiv:1706.03762
python task1.py
python task2.py
python task3.py
python task4.py
python task5.py window                  
python task6.py
python make_report.py
```

Ключ API зберігається у файлі `.env` (див. `.env.example`) і в репозиторій не додається.
