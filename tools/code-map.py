# -*- coding: utf-8 -*-
"""Карта крупных файлов прототипа: что где лежит и с какой строки.

styles.css, theme.css и app.js вместе весят больше 220 КБ. Читать их целиком,
чтобы поправить одно правило, — дорого и незачем. Скрипт собирает оглавление с
номерами строк, чтобы можно было открыть нужный кусок диапазоном.

Запуск:  python tools/code-map.py          — записать docs/code-map.md
         python tools/code-map.py --show   — вывести в консоль
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "code-map.md")
FILES = ["styles.css", "theme.css", "app.js"]

CSS_SEC = re.compile(r"^/\*\s*(.+?)(?:\*/)?\s*$")
JS_SEC = re.compile(r"^\s*/\*[=\s─]*\s*(.+?)(?:\s*[=─\s]*\*/)?\s*$")
JS_FN = re.compile(r"^\s{0,4}(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")


def markers(path, name):
    lines = io.open(path, encoding="utf-8").read().split("\n")
    out = []
    for i, l in enumerate(lines, 1):
        if name.endswith(".css"):
            if l.startswith("/*"):
                m = CSS_SEC.match(l)
                t = (m.group(1) if m else l).strip(" */")
                if t and not t.startswith("КООПТЕХ"):
                    out.append((i, "раздел", t))
        else:
            m = JS_FN.match(l)
            if m:
                out.append((i, "функция", m.group(1) + "()"))
                continue
            if l.strip().startswith("/*") and len(l.strip()) > 4:
                m = JS_SEC.match(l)
                t = (m.group(1) if m else l).strip(" */=─")
                if t and not t.startswith("КООПТЕХ") and len(t) > 3:
                    out.append((i, "раздел", t))
    return out, len(lines)


def trim(t, n=78):
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


blocks = [
    "# Карта крупных файлов прототипа\n",
    "Собирается `python tools/code-map.py` — правь код, не этот файл.\n",
    "Читай по диапазону, а не целиком: `sed -n '120,180p' styles.css` "
    "или `Read` с `offset`/`limit`. Номер строки — начало блока, "
    "конец — строка перед следующим.\n",
]
for name in FILES:
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        continue
    ms, total = markers(path, name)
    size = os.path.getsize(path) // 1024
    blocks.append(f"\n## {name} — {size} КБ, {total} строк, меток {len(ms)}\n")
    blocks.append("| Строка | | Что |\n|---:|---|---|")
    for ln, kind, t in ms:
        blocks.append(f"| {ln} | {kind} | {trim(t)} |")
    blocks.append("")

text = "\n".join(blocks) + "\n"
if "--show" in sys.argv:
    print(text)
else:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print(f"записано: {os.path.relpath(OUT, ROOT)} ({len(text)//1024} КБ)")
