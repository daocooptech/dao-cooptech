# -*- coding: utf-8 -*-
"""Проставить картинкам width/height и loading="lazy".

Пункты 11 и 12 аудита от 2026-09-08. Без width/height браузер не знает
пропорций до загрузки файла, и вёрстка прыгает на каждом каталоге, пока
подтягиваются фотографии. Размеры берутся настоящие, из самих файлов, —
это подсказка о пропорциях, отображением по-прежнему управляет CSS.

loading="lazy" не ставится первым трём картинкам страницы: то, что видно
сразу, грузить лениво незачем, это только замедляет первый экран.

Запуск:  python tools/img-attrs.py           — показать, что изменится
         python tools/img-attrs.py --apply   — записать
"""
import re, io, os, glob, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
APPLY = "--apply" in sys.argv
# Эталоны шапки и сайдбара правим вместе со страницами: иначе tools/check.py
# справедливо ругается, что страницы разошлись с шаблоном.
PAGES = sorted(glob.glob("*.html")) + ["tools/shell.html", "tools/shell-public.html"]

sizes = {}


def size_of(src):
    src = src.split("?")[0].split("#")[0]
    if src in sizes:
        return sizes[src]
    if not os.path.exists(src) or src.endswith(".svg"):
        sizes[src] = None
        return None
    try:
        with Image.open(src) as im:
            sizes[src] = im.size
    except Exception:
        sizes[src] = None
    return sizes[src]


IMG = re.compile(r"<img\b[^>]*>", re.I)
stat = {"width/height": 0, "lazy": 0, "без размера": 0, "всего": 0}
changed_pages = []

for page in PAGES:
    s = io.open(page, encoding="utf-8").read()
    out, last, n_page, idx = [], 0, 0, 0
    for m in IMG.finditer(s):
        tag = m.group(0)
        stat["всего"] += 1
        idx += 1
        src = re.search(r'\bsrc="([^"]+)"', tag)
        new = tag
        if src and "width=" not in tag and "height=" not in tag:
            wh = size_of(src.group(1))
            if wh:
                new = new[:-1].rstrip("/").rstrip() + f' width="{wh[0]}" height="{wh[1]}">'
                stat["width/height"] += 1
            else:
                stat["без размера"] += 1
        # первые три картинки страницы видны сразу — их лениво не грузим
        if "loading=" not in new and idx > 3:
            new = new[:-1].rstrip("/").rstrip() + ' loading="lazy">'
            stat["lazy"] += 1
        if new != tag:
            out.append(s[last:m.start()])
            out.append(new)
            last = m.end()
            n_page += 1
    if n_page:
        out.append(s[last:])
        changed_pages.append((page, n_page))
        if APPLY:
            io.open(page, "w", encoding="utf-8", newline="\n").write("".join(out))

print(f"картинок всего: {stat['всего']}")
print(f"  проставлено width/height: {stat['width/height']}")
print(f"  проставлено loading=lazy: {stat['lazy']}")
print(f"  без размера (файл не найден или svg): {stat['без размера']}")
print(f"  страниц затронуто: {len(changed_pages)}")
for p, n in sorted(changed_pages, key=lambda x: -x[1])[:8]:
    print(f"     {n:>4}  {p}")
print("\nзаписано" if APPLY else "\n(пробный запуск; --apply чтобы записать)")
