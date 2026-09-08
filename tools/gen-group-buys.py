# -*- coding: utf-8 -*-
"""Наполнение совместных закупок и связывание с экраном закупки.

Решения 252, 259–262: механика стола заказов развивается из «Совместных
закупок». Пятнадцать написанных вручную закупок сохраняются как есть, к ним
добавляются остальные из настоящих ресурсов, организаций и людей каталога.

Запуск:  python tools/gen-group-buys.py
"""
import re, io, os, json, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
random.seed(20260908)

PAGE = "ext-group-buying.html"


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def data(name):
    raw = rd(f"data/{name}.js")
    return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


PEOPLE, ORGS, RES = data("people"), data("organizations"), data("resources")

# точки выдачи берём из самой страницы точек, чтобы ссылки вели на живые места
pp = rd("pickup-points.html")
POINTS = re.findall(r'data-city="([^"]+)">\s*<div[^>]*>\s*<div[^>]*>\s*'
                    r'<div style="font-weight:600;font-size:14px">([^<]+)</div>', pp)
if not POINTS:
    POINTS = [("Тюмень", "Цех кооператива")]

UNITS = [("тонна", 8, 60), ("мешок", 40, 400), ("упаковка", 30, 300),
         ("штука", 20, 500), ("кг", 100, 2000), ("литр", 80, 1500),
         ("рулон", 15, 150), ("комплект", 10, 90), ("куб. м", 5, 80)]
CATS = ["Для дома и дачи · стройматериалы", "Продовольствие · бакалея",
        "Продовольствие · молочное", "Сельское хозяйство · корма",
        "Сельское хозяйство · семена и саженцы", "Инструмент и оборудование",
        "Упаковка и тара", "Хозяйственные товары", "Топливо и энергия",
        "Одежда и спецодежда"]
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
          "августа", "сентября", "октября", "ноября", "декабря"]


def existing(js):
    """Пятнадцать закупок, написанных вручную, — сохраняем дословно."""
    m = re.search(r"var GROUP_BUYS = \[", js)
    if not m:
        return [], None, None
    depth, i = 1, m.end()
    while depth:
        depth += 1 if js[i] == "[" else -1 if js[i] == "]" else 0
        i += 1
    return js[m.end():i - 1], m.start(), i + 1        # тело, начало, конец с ';'


def gen(n, taken_ids):
    out = []
    for k in range(n):
        r = random.choice(RES)
        o = random.choice(ORGS)
        p = random.choice(PEOPLE)
        city, point = random.choice(POINTS)
        unit, lo, hi = random.choice(UNITS)
        goal = random.randint(lo, hi)
        # состояния разные: набирается, почти набрана, набрана, провалилась
        state = random.choices(["idle", "near", "full", "weak"], [6, 3, 2, 2])[0]
        collected = {"idle": random.randint(int(goal * .15), int(goal * .6)),
                     "near": random.randint(int(goal * .75), goal - 1),
                     "full": random.randint(goal, int(goal * 1.3)),
                     "weak": random.randint(1, max(1, int(goal * .12)))}[state]
        base = random.randint(6, 900) * 100
        tiers = [
            {"upTo": round(goal * .3), "price": base, "label": f"до {round(goal * .3)} {unit}"},
            {"upTo": round(goal * .75), "price": round(base * .88 / 10) * 10,
             "label": f"{round(goal * .3)}–{round(goal * .75)}"},
            {"upTo": "Infinity", "price": round(base * .76 / 10) * 10,
             "label": f"{round(goal * .75)} {unit} и больше"},
        ]
        gid = re.sub(r"[^a-z0-9]+", "-", r["id"].encode("ascii", "ignore").decode().lower()).strip("-")
        gid = (gid or "gb") + f"-{k + 1}"
        while gid in taken_ids:
            gid += "x"
        taken_ids.add(gid)
        out.append({
            "id": gid,
            "title": r["title"][:70],
            "image": r.get("img", "images/photos/toolbox.jpg"),
            # категорию берём у самого ресурса, а не случайную: иначе мотоблок
            # оказывается в «Продовольствие · молочное», и всё наполнение
            # перестаёт выглядеть настоящим
            "category": " · ".join(x for x in [r.get("category"), r.get("subcategory")] if x)[:70]
                        or random.choice(CATS),
            "organizer": {"name": p["name"], "avatar": p["avatar"],
                          "link": f'person.html?id={p["id"]}'},
            "supplier": o["title"],
            "supplierLink": f'organization.html?id={o["id"]}',
            "unit": unit,
            "collected": collected,
            "goal": goal,
            "participants": max(1, round(collected / max(1, goal) * random.randint(8, 40))),
            "stopDate": f"{random.randint(1, 28)} {random.choice(MONTHS[8:11])} 2026",
            "pickupPoint": f"{point}, {city}",
            "pickupLink": "pickup-points.html",
            "orgFeePct": random.choice([2, 2.5, 3, 3.5, 4, 5]),
            "state": state,
            "tiers": tiers,
        })
    return out


# Написанные вручную закупки при первом запуске вынимаются со страницы и
# кладутся отдельно. Дальше берутся уже оттуда: после первого прогона на
# странице массива нет, и повторный запуск иначе терял бы их.
MANUAL = "data/_group-buys-manual.js"
if os.path.exists(MANUAL):
    kept = rd(MANUAL).split("=", 1)[1].rstrip().rstrip(";").strip()[1:-1].strip().rstrip(",")
else:
    js_all = "".join(re.findall(r"<script>(.*?)</script>", rd(PAGE), re.S))
    body, _, _ = existing(js_all)
    if not isinstance(body, str):
        raise SystemExit("исходный массив не найден и нет " + MANUAL)
    kept = body.strip().rstrip(",")
    os.makedirs("data", exist_ok=True)
    wr(MANUAL, "/* Закупки, написанные вручную. Отсюда их берёт tools/gen-group-buys.py,\n"
               "   чтобы повторный запуск их не потерял. Правь здесь. */\n"
               "window.GROUP_BUYS_MANUAL = [" + kept + "\n];\n")
    print("сохранены вручную написанные закупки в", MANUAL)
taken = set(re.findall(r"id: '([^']+)'", kept))
print(f"написанных вручную: {len(taken)}")

new = gen(105, set(taken))
new_js = ",\n    ".join(
    json.dumps(x, ensure_ascii=False).replace('"Infinity"', "Infinity") for x in new)

out = ("/* Совместные закупки. Первые записи написаны вручную и сохраняются;\n"
       "   остальные собирает tools/gen-group-buys.py из каталогов ресурсов,\n"
       "   организаций и людей — поставщики, организаторы и точки настоящие. */\n"
       "window.GROUP_BUYS = [" + kept + ",\n    " + new_js + "\n];\n")
os.makedirs("data", exist_ok=True)
wr("data/group-buys.js", out)
print(f"data/group-buys.js: закупок {len(taken) + len(new)} ({len(out)//1024} КБ)")

# страница читает данные из файла
s = rd(PAGE)
s2 = s[:s.index("var GROUP_BUYS = [")] + "var GROUP_BUYS = window.GROUP_BUYS || [];" + \
     s[s.index("];", s.index("var GROUP_BUYS = [")) + 2:]
if "data/group-buys.js" not in s2:
    s2 = s2.replace("<script>", '<script src="data/group-buys.js"></script>\n<script>', 1)
# заголовок карточки ведёт на экран закупки
s2 = s2.replace(
    "'<div class=\"gb-title\">' + escapeHtml(gb.title) + '</div>' +",
    "'<div class=\"gb-title\"><a href=\"group-buy.html?id=' + encodeURIComponent(gb.id) + '\">'"
    " + escapeHtml(gb.title) + '</a></div>' +", 1)
wr(PAGE, s2)
print(f"{PAGE}: данные вынесены в файл, заголовки ведут на group-buy.html")
