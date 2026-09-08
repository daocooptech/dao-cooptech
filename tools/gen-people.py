# -*- coding: utf-8 -*-
"""Собрать data/people.js из каталога people.html.

Имена, фото, города, доверие, навыки и специализация берутся из карточек
каталога — они подобраны осмысленно и остаются источником истины. Достраиваются
только поля, которых в карточке нет, но которые показывает детальная страница:
телефон, дата рождения, языки, баланс, число сделок и отзывов, подписчики,
мессенджеры, приложения. Достраиваются детерминированно от идентификатора,
поэтому у человека всегда одни и те же данные между запусками.

Запуск:  python tools/gen-people.py
"""
import re, io, os, json, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

REGION = {
    "Москва": "495", "Санкт-Петербург": "812", "Новосибирск": "383", "Екатеринбург": "343",
    "Казань": "843", "Нижний Новгород": "831", "Челябинск": "351", "Самара": "846",
    "Омск": "381", "Ростов-на-Дону": "863", "Уфа": "347", "Красноярск": "391",
    "Воронеж": "473", "Пермь": "342", "Волгоград": "844", "Краснодар": "861",
    "Саратов": "845", "Тюмень": "345", "Иркутск": "395", "Хабаровск": "421",
    "Владивосток": "423", "Томск": "382", "Сочи": "862", "Калининград": "401",
    "Ярославль": "485", "Барнаул": "385", "Кемерово": "384", "Ижевск": "341",
}
# Только правдоподобные пары «город — второй язык»: титульный язык республики
# либо язык заметной местной общины. Не приписывать людям языки соседних
# регионов: житель Красноярска с якутским языком выглядит выдумкой, и это
# первое, за что цепляется глаз.
LANG_BY_CITY = {
    "Казань": "Татарский", "Уфа": "Башкирский", "Ижевск": "Удмуртский",
    "Хабаровск": "Китайский", "Владивосток": "Корейский", "Калининград": "Немецкий",
    "Краснодар": "Армянский", "Сочи": "Армянский",
}
MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]
MSG = [["Telegram"], ["Telegram", "WhatsApp"], ["WhatsApp", "Viber"],
       ["Telegram", "WhatsApp", "Viber"], ["Telegram", "Max"]]
APPS = [[], ["GitHub"], ["GitHub", "Habr"], ["Дзен"], ["VK"], ["GitHub", "VK"]]

TRANSLIT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
            "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
            "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}


def translit(s):
    return "".join(TRANSLIT.get(c, c if c.isalnum() else "") for c in s.lower())


def attr(b, name):
    m = re.search(rf'{name}="([^"]*)"', b)
    return m.group(1) if m else ""


def h(slug, salt, mod):
    return int(hashlib.sha1(f"{slug}:{salt}".encode()).hexdigest(), 16) % mod


src = io.open("people.html", encoding="utf-8").read()
starts = [m.start() for m in re.finditer(r'<a\b[^>]*class="vacancy-card"', src)]
blocks = [src[starts[i]: starts[i + 1] if i + 1 < len(starts) else len(src)]
          for i in range(len(starts))]

people = []
for b in blocks:
    slug = attr(b, "data-fav-id")
    if not slug:
        continue
    m = re.search(r'<img class="avatar" src="([^"]+)" alt="([^"]+)"', b)
    if not m:
        continue
    avatar, name = m.group(1), m.group(2)
    city = attr(b, "data-city")
    parts = name.split()
    handle = (translit(parts[1]) + "-" + translit(parts[0])) if len(parts) > 1 else translit(name)

    # Доля отзывов должна сходиться с процентом доверия из карточки: «92%»
    # рядом с «57 из 59» — это 96%, и такое расхождение сразу видно на экране.
    trust = int(attr(b, "data-trust") or 0)
    # Знаменатель подбирается так, чтобы доля отзывов давала ровно тот процент,
    # что стоит в карточке каталога. При малом числе сделок процент вида 92%
    # просто не выражается дробью, и на экране получается «92% (3/3)».
    # 99% требует минимум сотни оценённых сделок, 97% — четвёртого десятка,
    # поэтому окно поиска широкое: у самых надёжных участников сделок и должно
    # быть много, иначе высокий процент сам по себе неправдоподобен.
    base = 18 + h(slug, "rated", 55)
    rated = base
    for r in list(range(base, 161)) + list(range(base - 1, 17, -1)):
        pos = round(r * trust / 100)
        if r and round(pos * 100 / r) == trust:
            rated = r
            break
    positive = max(0, min(rated, round(rated * trust / 100)))
    deals = rated + h(slug, "unrated", 5)
    langs = ["Русский"]
    if city in LANG_BY_CITY and h(slug, "l", 3):
        langs.append(LANG_BY_CITY[city])
    if h(slug, "en", 4) == 0:
        langs.append("Английский")

    people.append({
        "id": slug,
        "name": name,
        "verified": "badge verified" in b,
        "avatar": avatar,
        "city": city,
        "trust": trust,
        "category": attr(b, "data-category"),
        "subcategory": attr(b, "data-subcategory"),
        "skills": [s for s in attr(b, "data-skills").split(",") if s],
        "phone": f"+7-{REGION.get(city, '900')}-{100 + h(slug, 'p1', 900)}-{1000 + h(slug, 'p2', 9000)}",
        "skype": handle,
        "birthday": f"{1 + h(slug, 'd', 28)} {MONTHS[h(slug, 'm', 12)]} {1962 + h(slug, 'y', 40)}",
        "languages": langs,
        "balance": (5 + h(slug, "bal", 400)) * 5000,
        "deals": deals,
        "rated": rated,
        "positive": positive,
        "subscribers": 4 + h(slug, "sub", 900),
        "messengers": MSG[h(slug, "msg", len(MSG))],
        "apps": APPS[h(slug, "app", len(APPS))],
    })

os.makedirs("data", exist_ok=True)
out = ("/* Данные каталога людей. Собирается tools/gen-people.py из people.html —\n"
       "   правь каталог, а не этот файл. */\n"
       "window.PEOPLE = " + json.dumps(people, ensure_ascii=False, indent=1) + ";\n")
io.open("data/people.js", "w", encoding="utf-8", newline="\n").write(out)
print(f"записей: {len(people)}, уникальных id: {len({p['id'] for p in people})}, "
      f"городов: {len({p['city'] for p in people})} → data/people.js ({len(out)//1024} КБ)")
