# -*- coding: utf-8 -*-
"""Собрать data/<раздел>.js из каталогов и связать карточки с детальными страницами.

Каталог остаётся источником истины: заголовки, фотографии, города и все
data-атрибуты берутся из самих карточек. Скрипт ничего не выдумывает —
он только вынимает то, что уже размечено, и проставляет ссылкам ?id.

Запуск:  python tools/gen-catalogs.py           — собрать и связать
         python tools/gen-catalogs.py --check   — только показать, что найдено
"""
import re, io, os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CHECK = "--check" in sys.argv

# каталог, детальная страница, класс карточки, имя набора данных
PAIRS = [
    ("resources.html", "resource.html", "ptile", "RESOURCES"),
    ("skills.html", "skill.html", "vacancy-card", "SKILLS"),
    ("vacancies.html", "vacancy.html", "vacancy-card", "VACANCIES"),
    ("projects.html", "project.html", "ptile", "PROJECTS"),
    ("organizations.html", "organization.html", "ptile", "ORGANIZATIONS"),
]
TITLE_CLS = r"(?:pname|vacancy-title|ptile-title|card-title)"


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


total = {}
for cat, det, cls, varname in PAIRS:
    s = rd(cat)
    starts = [m.start() for m in re.finditer(rf'<a\b[^>]*href="{det}[^"]*"', s)]
    if not starts:
        print(f"{cat}: ссылок на {det} нет — пропущено")
        continue
    blocks = [s[starts[i]: starts[i + 1] if i + 1 < len(starts) else min(len(s), starts[i] + 4000)]
              for i in range(len(starts))]

    seen, records = set(), []
    for b in blocks:
        # атрибуты берём ТОЛЬКО из открывающего тега ссылки: если сканировать
        # весь блок, в запись попадают data-* вложенных элементов и соседней
        # карточки, и у проекта оказывается чужой город с чужой готовностью.
        tag = re.match(r"<a\b[^>]*>", b)
        if not tag:
            continue
        tag = tag.group(0)
        m = re.search(r'data-fav-id="([^"]+)"', tag)
        if not m:
            continue
        rid = m.group(1)
        rec = {"id": rid}
        for k, v in re.findall(r'\bdata-([a-z-]+)="([^"]*)"', tag):
            if k != "fav-id":
                rec[k.replace("-", "_")] = v
        t = re.search(rf'class="[^"]*{TITLE_CLS}[^"]*"[^>]*>([^<]{{2,120}})', b)
        rec["title"] = t.group(1).strip() if t else rid
        img = re.search(r'<img[^>]+src="([^"]+)"(?:[^>]*alt="([^"]*)")?', b)
        if img:
            rec["img"] = img.group(1)
            rec["alt"] = (img.group(2) or rec["title"]).strip()
        if rid not in seen:            # человек может стоять на нескольких полках
            seen.add(rid)
            records.append(rec)

    total[cat] = (len(starts), len(records))
    print(f"{cat:<22} карточек {len(starts):>4}, уникальных записей {len(records):>4}"
          f"  → data/{cat[:-5]}.js")
    if CHECK:
        print("   пример:", json.dumps(records[0], ensure_ascii=False)[:200])
        continue

    os.makedirs("data", exist_ok=True)
    out = (f"/* Данные каталога. Собирается tools/gen-catalogs.py из {cat} —\n"
           f"   правь каталог, а не этот файл. */\n"
           f"window.{varname} = " + json.dumps(records, ensure_ascii=False, indent=1) + ";\n")
    wr(f"data/{cat[:-5]}.js", out)

    # ссылки: каждой карточке свой ?id
    n = 0

    def relink(m):
        global n
        tag = m.group(0)
        fav = re.search(r'data-fav-id="([^"]+)"', tag)
        if not fav or "?id=" in tag:
            return tag
        n += 1
        return tag.replace(f'href="{det}"', f'href="{det}?id={fav.group(1)}"', 1)

    s2 = re.sub(rf'<a\b[^>]*href="{det}"[^>]*>', relink, s)
    wr(cat, s2)
    print(f"{'':<22} ссылок связано {n}")

# ── сделки размечены иначе ─────────────────────────────────────────────
# У них нет data-fav-id: карточка это <article class="deal-card"> с набором
# атрибутов, а идентификатор — номер сделки вида СД-2026-000102, который лежит
# в data-search. Ссылка «Открыть сделку» одна на карточку и ведёт без параметра.
s = rd("deals.html")
starts = [m.start() for m in re.finditer(r'<article\b[^>]*class="deal-card"', s)]
records, seen, linked = [], set(), 0
pieces, prev = [], 0
for i, st in enumerate(starts):
    end = starts[i + 1] if i + 1 < len(starts) else len(s)
    card = s[st:end]
    tag = re.match(r"<article\b[^>]*>", card).group(0)
    num = re.search(r"[СсSs][ДдDd]-\d{4}-\d{6}", card)
    if not num:
        continue
    rid = num.group(0).upper()
    rec = {"id": rid}
    for k, v in re.findall(r'\bdata-([a-z-]+)="([^"]*)"', tag):
        if k != "search":
            rec[k.replace("-", "_")] = v
    t = re.search(r'class="deal-title"[^>]*>([^<]{2,140})', card)
    rec["title"] = t.group(1).strip() if t else rid
    if rid not in seen:
        seen.add(rid)
        records.append(rec)
    card2, n2 = re.subn(r'(<a class="deal-link" href="deal\.html)"',
                        rf'\1?id={rid}"', card, count=1)
    linked += n2
    pieces.append((st, end, card2))

if pieces:
    out_s, last = [], 0
    for st, end, card2 in pieces:
        out_s.append(s[last:st]); out_s.append(card2); last = end
    out_s.append(s[last:])
    print(f"{'deals.html':<22} карточек {len(starts):>4}, уникальных записей {len(records):>4}"
          f"  → data/deals.js")
    print(f"{'':<22} ссылок связано {linked}")
    if not CHECK:
        wr("deals.html", "".join(out_s))
        wr("data/deals.js",
           "/* Данные реестра сделок. Собирается tools/gen-catalogs.py из deals.html —\n"
           "   правь каталог, а не этот файл. */\n"
           "window.DEALS = " + json.dumps(records, ensure_ascii=False, indent=1) + ";\n")
    total["deals.html"] = (len(starts), len(records))

if CHECK:
    print("\nпример сделки:", json.dumps(records[0], ensure_ascii=False)[:220] if records else "нет")
    sys.exit(0)
print("\nитого:", ", ".join(f"{k.split('.')[0]} {v[1]}" for k, v in total.items()))
