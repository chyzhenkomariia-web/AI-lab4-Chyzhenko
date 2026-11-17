"""Витягує текст із PDF і зберігає в data/long_text.txt.

Використання:  python pdf_to_txt.py attention.pdf

Список літератури (усе після заголовка References) відкидається,
бо він не несе змісту для узагальнення.
"""
import re
import sys
from pathlib import Path

from pypdf import PdfReader

if len(sys.argv) < 2:
    raise SystemExit("Вкажіть шлях до PDF: python pdf_to_txt.py attention.pdf")

reader = PdfReader(sys.argv[1])
text = "\n".join(page.extract_text() or "" for page in reader.pages)

cut = re.search(r"\n\s*References\s*\n", text)
if cut:
    text = text[:cut.start()]
text = re.sub(r"-\n(\w)", r"\1", text)      # переноси слів
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n{3,}", "\n\n", text).strip()

out = Path(__file__).parent / "data" / "long_text.txt"
out.write_text(text, encoding="utf-8")
print(f"Сторінок: {len(reader.pages)}, символів: {len(text)}, слів: {len(text.split())}")
print(f"Збережено: {out}")
