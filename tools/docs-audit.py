# -*- coding: utf-8 -*-
"""Сверка документации с тем, что построено.

`docs/mvp-spec.md` — источник истины по функциональности v1, но решений с тех
пор принято больше трёхсот, и часть спецификации разошлась с прототипом.
Скрипт ищет расхождения, которые можно проверить механически: упоминания
несуществующих страниц, устаревшие числа, утверждения о том, что уже сделано.

Запуск:  python tools/docs-audit.py
"""
import re, io, os, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
DOCS = sorted(glob.glob("docs/*.md"))
PAGES = {os.path.basename(p) for p in glob.glob("*.html")}


def rd(p):
    return io.open(p, encoding="utf-8").read()


issues = collections.defaultdict(list)

# 1. ссылки на страницы
for d in DOCS:
    t = rd(d)
    for m in re.finditer(r"`([a-z0-9\-]+\.html)`", t):
        if m.group(1) not in PAGES:
            issues["Ссылки на несуществующие страницы"].append(f"{d}: {m.group(1)}")

# 2. страницы, которых в документации нет вовсе
mentioned = set()
for d in DOCS:
    mentioned |= set(re.findall(r"`([a-z0-9\-]+\.html)`", rd(d)))
missing = sorted(PAGES - mentioned)
for p in missing:
    issues["Страницы, не описанные ни в одном документе"].append(p)

# 3. устаревшие утверждения о числе разделов
for d in DOCS:
    t = rd(d)
    for m in re.finditer(r"(восемь|восьми|8)\s+(основных\s+)?раздел\w*", t, re.I):
        line = t[:m.start()].count("\n") + 1
        issues["«Восемь разделов» — их одиннадцать плюс расширения"].append(f"{d}:{line}")

# 4. утверждения о статичности детальных страниц — уже неверны (решение 253)
STALE = [
    (r"стати(чн|ческ)\w*.{0,80}детальн|детальн\w+.{0,80}стати(чн|ческ)",
     "детальные страницы названы статичными — решение 253 это отменило"),
    (r"один и тот же (демо-)?экземпляр",
     "«один и тот же экземпляр» — страницы читают ?id с 2026-09-08"),
    # ловим именно неверное утверждение, а не любое упоминание настройки:
    # фраза «prefers-color-scheme не учитывается» — верная и флагом быть не должна
    (r"(следует|идёт|ориентируется)\s+за\s+системн\w+|системн\w+\s+тем\w+\s+по умолчанию",
     "тема: без выбора пользователя всегда светлая, системная не учитывается (fc9582c)"),
    (r"\bоргсбор\w*\s+включ[её]н",
     "«оргсбор включён в цену» — решение 255/261 требует показывать строкой"),
]
# Текст, который сам сообщает, что утверждение снято, — не расхождение, а его
# исправление. Без этого проверка ловит собственную правку и никогда не сходится.
CORRECTED = re.compile(r"~~|исправлено|устарело|перестал|отменено|сделано \d{4}-", re.I)
for d in DOCS:
    t = rd(d)
    lines = t.split("\n")
    for rx, why in STALE:
        for m in re.finditer(rx, t, re.I):
            line = t[:m.start()].count("\n")
            around = " ".join(lines[max(0, line - 2):line + 3])
            if CORRECTED.search(around):
                continue
            ctx = re.sub(r"\s+", " ", t[max(0, m.start() - 60):m.end() + 60])
            issues["Утверждения, отменённые решениями"].append(
                f"{d}:{line + 1} — {why}\n        …{ctx}…")

# 5. разделы, появившиеся после спецификации
spec = rd("docs/mvp-spec.md")
for name, page in [("Сообщества", "communities.html"), ("Кошелёк", "wallet.html"),
                   ("Сделки", "deals.html"), ("Совместные закупки", "ext-group-buying.html"),
                   ("Стол заказов", "group-buy.html"), ("Токеномика", "tokenomics.html")]:
    if page not in spec:
        issues["Разделы меню, отсутствующие в спецификации"].append(f"{name} ({page})")

print(f"документов: {len(DOCS)}, страниц: {len(PAGES)}\n")
total = 0
for kind, items in issues.items():
    total += len(items)
    print(f"── {kind} — {len(items)}")
    for it in items[:14]:
        print(f"     {it}")
    if len(items) > 14:
        print(f"     … и ещё {len(items) - 14}")
    print()
print(f"всего расхождений: {total}")
