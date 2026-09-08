# -*- coding: utf-8 -*-
"""Наполнение разделов-действий: уведомления, точки самовывоза, реестры активов.

Решение 254: правило «не менее 100–200 записей» распространяется не только на
каталоги сущностей, но и на экраны действий. Данные берутся из уже собранных
data/*.js — люди, организации, ресурсы и проекты настоящие, те же, что в
каталогах, поэтому уведомление про «Иванову Марию» ведёт на существующего
человека, а не в пустоту.

Запуск:  python tools/fill-actions.py
"""
import re, io, os, json, hashlib, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
random.seed(20260908)          # воспроизводимость: один и тот же запуск даёт одно и то же


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def data(name):
    raw = rd(f"data/{name}.js")
    return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


PEOPLE = data("people")
ORGS = data("organizations")
RES = data("resources")
PROJ = data("projects")
DEALS = data("deals")
CITIES = sorted({p["city"] for p in PEOPLE if p.get("city")})

MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
          "июля", "августа", "сентября", "октября", "ноября", "декабря"]


def plural(n, one, few, many):
    """Согласование числительного: 1 час, 2 часа, 5 часов.

    Без этого получается «6 часа назад» и «3 минут назад» — мелочь, за которую
    носитель языка цепляется мгновенно и перестаёт верить остальному.
    """
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def ago(n, one, few, many):
    return f"{n} {plural(n, one, few, many)} назад"


def when(i):
    """Чем старее уведомление, тем грубее отметка времени — как в жизни."""
    if i < 4:
        return ago(random.choice([1, 3, 5, 12, 27, 40]), "минуту", "минуты", "минут")
    if i < 12:
        return ago(random.randint(1, 9), "час", "часа", "часов")
    if i < 18:
        return "вчера"
    if i < 40:
        return ago(random.randint(2, 6), "день", "дня", "дней")
    if i < 70:
        return ago(random.randint(2, 3), "неделю", "недели", "недель")   # «1 неделю назад» звучит криво
    # Абсолютные даты только в прошлом: уведомление, датированное будущим,
    # выглядит поломкой сильнее, чем отсутствие уведомлений вообще.
    return f"{random.randint(1, 28)} {random.choice(['июня', 'июля', 'августа'])}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inner_span(s, open_tag_end):
    """Границы содержимого <div>, открытого до позиции open_tag_end.

    Считаем по балансу тегов, а не «до ближайшего </div>»: на глаз граница
    блока определяется неверно, и в разметке появляется лишний или недостающий
    закрывающий тег — ровно это и поймала tools/check.py на первом заходе.
    """
    depth, i = 1, open_tag_end
    tag = re.compile(r"</?div\b", re.I)
    while depth:
        m = tag.search(s, i)
        if not m:
            raise SystemExit("не найден закрывающий </div> — разметка не тронута")
        depth += -1 if m.group(0).startswith("</") else 1
        i = m.end()
    return open_tag_end, i - len(m.group(0))


# ── 1. уведомления ─────────────────────────────────────────────────────
def notifications(n=140):
    out = []
    for i in range(n):
        p = random.choice(PEOPLE)
        o = random.choice(ORGS)
        r = random.choice(RES)
        pr = random.choice(PROJ)
        dl = random.choice(DEALS)
        pl = f'<a href="person.html?id={p["id"]}">{esc(p["name"])}</a>'
        ol = f'<a href="organization.html?id={o["id"]}">{esc(o["title"])}</a>'
        rl = f'<a href="resource.html?id={r["id"]}">{esc(r["title"])}</a>'
        prl = f'<a href="project.html?id={pr["id"]}">{esc(pr["title"])}</a>'
        dll = f'<a href="deal.html?id={dl["id"]}">{dl["id"]}</a>'
        # Про организации пишем без глаголов в прошедшем времени: у «ООО»,
        # «Кооператива» и «Артели» разный род, и одна формулировка на всех
        # неизбежно даёт «Кооператив подтвердило».
        # Род определяем по отчеству, а не по имени: «Никита» и «Илья»
        # оканчиваются на гласную, но это мужчины.
        parts = p["name"].split()
        fem = len(parts) > 2 and parts[2].endswith(("на", "кызы"))
        did = lambda v: v + ("а" if fem else "")
        t = random.choice([
            f'{pl} {did("подал")} заявку на участие в проекте «{prl}».',
            f'{pl} {did("оставил")} отзыв по сделке {dll} — оценка положительная.',
            f'Новый ресурс от {ol}: {rl}.',
            f'Отклик на вашу вакансию — {pl}.',
            f'Сделка {dll} перешла в статус «ожидает приёмки».',
            f'По сделке {dll} открыт спор — требуется ваше решение.',
            f'Сделка {dll} отменена второй стороной.',
            f'{pl} {did("подписал")}ся на ваши новости.',
            f'Приглашение в сообщество от {ol}.',
            f'Голосование в проекте «{prl}» завершится через два дня.',
            f'Взаимозачёт с {ol} проведён.',
            f'{pl} {did("предложил")} обмен на ресурс {rl}.',
            f'Оплата по сделке {dll} поступила на паевой счёт.',
            f'Партия по совместной закупке набрана — {rl} уходит в отгрузку.',
            f'Приёмка партии на пункте выдачи подтверждена: {ol}.',
            f'Ваше объявление {rl} висит без просмотров вторую неделю.',
            f'{pl} {did("завершил")} задачу в проекте «{prl}».',
            f'Уровень доверия обновлён после сделки {dll}.',
        ])
        read = " read" if i >= 18 else ""
        out.append(
            f'          <div class="notif-item"><div class="notif-dot{read}"></div>'
            f'<div>{t}<div class="ntime">{when(i)}</div></div></div>')
    return "\n".join(out)


s = rd("notifications.html")
m = re.search(r'<div class="notif-list">', s)
a, b = inner_span(s, m.end())
body = notifications()
s = s[:a] + "\n" + body + "\n        " + s[b:]
wr("notifications.html", s)
print(f"notifications.html: уведомлений {body.count('notif-item')}, "
      f"из них непрочитанных {body.count('notif-dot\"')}")

# модификатор «прочитано» — рядом с родным правилом
c = rd("styles.css")
if ".notif-dot.read" not in c:
    old = ".notif-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--gold); margin-top: 5px; flex: none; }"
    new = old + "\n/* Прочитанное: точка сохраняет место, чтобы строки не разъезжались. */\n.notif-dot.read { background: transparent; }"
    c = c.replace(old, new, 1)
    wr("styles.css", c)
    print("styles.css: добавлен .notif-dot.read")

# ── 2. точки самовывоза ────────────────────────────────────────────────
STREETS = ["ул. Мельникайте", "пр. Ленина", "ул. Советская", "ул. Гагарина",
           "ул. Кирова", "ул. Мира", "пр. Победы", "ул. Заводская",
           "ул. Полевая", "ул. Строителей", "ул. Кооперативная", "ул. Садовая",
           "пер. Северный", "ул. Луговая", "ш. Восточное", "ул. Речная"]
KINDS = [
    ("Цех кооператива", "Собственное производственное помещение — самовывоз и приём заказов."),
    ("Склад участка", "Складской участок кооператива: приём партий и выдача заказов."),
    ("Сельский магазин", "Магазин пайщика: выдача заказов в часы работы торговой точки."),
    ("Пункт при ферме", "Выдача прямо с фермы, свежие партии по графику отгрузки."),
    ("Коворкинг", "Выдача мелких заказов и документов в рабочие часы."),
    ("Мастерская", "Выдача изделий и приём материалов от поставщиков."),
    ("Кооперативная лавка", "Постоянная точка кооператива в жилом районе."),
    ("Пекарня", "Выдача продуктовых заказов и своя выпечка."),
    ("Автостанция", "Транзитный пункт — выдача заказов проезжающим."),
    ("Библиотека", "Партнёрская точка: выдача небольших посылок и книг."),
]
HOURS = ["Пн–Пт 9:00–18:00", "Пн–Сб 8:00–20:00", "Ежедневно 10:00–19:00",
         "Пн–Пт 10:00–17:00, Сб 10:00–14:00", "Вт–Вс 9:00–21:00",
         "Круглосуточно", "По договорённости"]


def points(n=26):
    """Решение 264: кооператив показывается на этапе первого года. Точек
    десятки, городов единицы — сто двадцать точек в тридцати одном городе
    это сеть размером с федеральную розницу, а не кооператив на старте."""
    # Города берём связным кустом вокруг одного центра, а не случайно по стране:
    # точки в Калининграде и Хабаровске одновременно — это не кооператив
    # первого года, а федеральная сеть. Опорный город — Тюмень: он же стоит в
    # написанных вручную закупках.
    CLUSTER = ["Тюмень", "Ишим", "Екатеринбург", "Курган", "Омск", "Челябинск",
               "Тобольск", "Сургут"]
    home = [c for c in CLUSTER if c in CITIES] or random.sample(CITIES, 5)
    out = []
    for i in range(n):
        city = random.choice(home)
        kind, desc = random.choice(KINDS)
        addr = f"{random.choice(STREETS)}, {random.randint(1, 180)}"
        chips = "".join(
            f'<a class="chip" href="resource.html?id={r["id"]}">{esc(r["title"][:34])}</a>'
            for r in random.sample(RES, random.randint(1, 3)))
        closed = (i % 17 == 0)
        badge = ('<span class="badge outline">Временно не работает</span>' if closed
                 else f'<span class="badge outline">{random.choice(HOURS)}</span>')
        note = ("<div style=\"color:var(--slate);font-size:12px;margin-top:10px\">"
                "Точка закрыта на ремонт, заказы переводятся на соседнюю.</div>"
                if closed else
                f'<div style="color:var(--slate);font-size:12px;margin-top:10px">{desc}</div>')
        out.append(f'''        <div class="card" style="padding:16px 18px" data-city="{city}">
          <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">
            <div>
              <div style="font-weight:600;font-size:14px">{kind} №{i + 1}</div>
              <div style="color:var(--slate);font-size:12.5px;margin-top:2px">📍 {city}, {addr}</div>
            </div>
            {badge}
          </div>
{note}
          <div class="filter-chips" style="margin-top:10px">{chips}</div>
        </div>''')
    return "\n".join(out)


s = rd("pickup-points.html")
cards = [m for m in re.finditer(r'<div class="card" style="padding:16px 18px" data-city=', s)]
if cards:
    first = cards[0].start()
    # конец последней карточки считаем по балансу тегов от её начала
    last_open_end = s.index(">", cards[-1].start()) + 1
    _, inner_end = inner_span(s, last_open_end)
    last_end = inner_end + len("</div>")
    body = points()
    s = s[:first] + body.lstrip() + s[last_end:]
    wr("pickup-points.html", s)
    print(f"pickup-points.html: точек {body.count('data-city=')}, было {len(cards)}")


# ── 3. реестры активов ─────────────────────────────────────────────────
def money(n):
    return f"{n:,}".replace(",", " ") + " ₽"


def rows_cfa(n=110):
    RIGHTS = ["Денежное требование", "Право участия",
              "Право по эмиссионным ценным бумагам", "Право требования передачи вещи",
              "Право требовать выполнения работ"]
    out = []
    for i in range(n):
        pr, o = random.choice(PROJ), random.choice(ORGS)
        kind = random.choice(["share", "pai", "token", "claim"])
        if kind == "share":
            share = round(random.uniform(0.5, 24.5), 1)
            title = f'Доля дохода — проект «{esc(pr["title"])}»'
            sub = f'эмитент: ДАО КООПТЕХ · <a href="project.html?id={pr["id"]}">открыть проект</a>'
            # «11,0%» выглядит машинно — целые доли пишем без хвоста
            qty = (f"{share:g}".replace(".", ",") + "%")
            right = "Денежное требование"
        elif kind == "pai":
            title = f'Пай — {esc(o["title"])}'
            sub = f'эмитент: {esc(o["title"])} · <a href="organization.html?id={o["id"]}">открыть организацию</a>'
            qty, right = f"{random.randint(1, 12)} пая" if random.randint(1, 12) > 1 else "1 пай", "Право участия"
        elif kind == "token":
            title = f'Токен {esc(o["title"])}'
            sub = f'эмитент: {esc(o["title"])} · <a href="organization.html?id={o["id"]}">открыть организацию</a>'
            qty, right = f"{random.randint(10, 4000)} шт.", "Право по эмиссионным ценным бумагам"
        else:
            r = random.choice(RES)
            title = f'Требование поставки — {esc(r["title"][:44])}'
            sub = f'эмитент: {esc(o["title"])} · <a href="resource.html?id={r["id"]}">открыть ресурс</a>'
            qty, right = f"{random.randint(1, 40)} ед.", "Право требования передачи вещи"
        val = random.randint(3, 900) * 500
        out.append(f'            <tr><td class="stage-head">{title}'
                   f'<div class="stage-sub" style="padding-left:0;font-weight:400">{sub}</div></td>'
                   f'<td>{right}</td><td>{qty}</td><td>{money(val)}</td></tr>')
    return "\n".join(out)


def rows_nma(n=100):
    TYPES = [("Средство индивидуализации", "средство индивидуализации"),
             ("Ноу-хау (секрет производства)", "результат интеллектуальной деятельности"),
             ("Результат интеллектуальной деятельности", "программа для ЭВМ"),
             ("Исключительное право на изобретение", "патент"),
             ("Исключительное право на полезную модель", "патент"),
             ("База данных", "результат интеллектуальной деятельности")]
    NAMES = ["Товарный знак", "Ноу-хау", "Исключительное право на ПО",
             "Патент на изобретение", "База данных", "Полезная модель",
             "Промышленный образец", "Секрет производства"]
    out = []
    for i in range(n):
        pr, o = random.choice(PROJ), random.choice(ORGS)
        t, sub_t = random.choice(TYPES)
        base = random.randint(40, 1800) * 1000
        forever = random.random() < 0.22
        if forever:
            spi, rest = "не определён", base
        else:
            years = random.choice([3, 4, 5, 7, 10])
            used = random.randint(0, years * 12 - 1)
            spi = f"{years} {plural(years, 'год', 'года', 'лет')}"
            rest = round(base * (1 - used / (years * 12)) / 100) * 100
        name = f'{random.choice(NAMES)} «{esc(pr["title"][:38])}»'
        link = (f'<a href="project.html?id={pr["id"]}">открыть проект</a>' if random.random() < .5
                else f'<a href="organization.html?id={o["id"]}">открыть организацию</a>')
        out.append(f'            <tr><td class="stage-head">{name}'
                   f'<div class="stage-sub" style="padding-left:0;font-weight:400">{sub_t} · {link}</div></td>'
                   f'<td>{t}</td><td>{money(base)}</td><td>{spi}</td><td>{money(rest)}</td></tr>')
    return "\n".join(out)


for page, gen, label in [("digital-assets.html", rows_cfa, "ЦФА"),
                         ("intangible-assets.html", rows_nma, "НМА")]:
    s = rd(page)
    m = re.search(r'<table class="res-table">', s)
    end = s.index("</table>", m.end())
    head = re.search(r"<tr><th>.*?</tr>", s[m.end():end], re.S)
    header = head.group(0) if head else ""
    body = gen()
    s = s[:m.end()] + "\n            " + header + "\n" + body + "\n          " + s[end:]
    wr(page, s)
    print(f"{page}: строк {label} {body.count('<tr>')}")


# ── 4. лента новостей проектов ─────────────────────────────────────────
# Лента рисуется из PROJECT_NEWS и показывает только те проекты, на которые
# участник подписан. Пустой она была не из-за логики, а из-за того, что
# новости были всего у двух проектов из ста.
POST_TEXTS = [
    "Присоединил{a}сь к проекту — буду отвечать за {role}.",
    "Поставлена новая задача: {task}. Срок — {weeks}.",
    "Задача выполнена: {task}. Переходим к следующему этапу.",
    "Провели встречу на площадке: обсудили {topic}, наметили план на месяц.",
    "Закупили {stuff} — как и планировали в разделе «Необходимые ресурсы».",
    "Этап завершён. Готовность проекта — {ready}%.",
    "Ищем {role}: если умеете и готовы вложиться временем, откликайтесь.",
    "Сдвигаем срок на {weeks}: поставщик задержал {stuff}.",
    "Открыто голосование по смете. Голоса считаем до конца недели.",
    "Отчёт за месяц: потратили {money}, остаток на паевом счёте виден в кошельке.",
    "Проблема: {problem}. Нужна помощь тех, кто сталкивался.",
    "Первая партия ушла заказчикам — спасибо всем, кто участвовал.",
]
ROLES = ["сварку каркаса", "закупки", "документы и отчётность", "логистику",
         "подбор материалов", "монтаж оборудования", "проектирование",
         "связь с пайщиками", "приёмку работ", "испытания"]
TASKS = ["рассчитать смету", "подготовить площадку", "собрать каркас",
         "заказать материалы", "согласовать документы", "провести испытания",
         "настроить оборудование", "нанять бригаду", "оформить приёмку"]
TOPICS = ["результаты испытаний", "смету на второй этап", "график поставок",
          "распределение долей", "план работ на осень"]
STUFF = ["двигатели", "профильную трубу", "кабель", "цемент", "утеплитель",
         "фурнитуру", "семена", "оборудование", "инструмент"]
PROBLEMS = ["не сходится смета по электрике", "поставщик поднял цену на 12%",
            "нужен второй сварщик на неделю", "не хватает места на складе",
            "задерживается подключение к сети"]
WEEKS = ["две недели", "месяц", "три недели", "десять дней"]


def feed_posts(pr, n):
    out = []
    hours = 1
    for k in range(n):
        p = random.choice(PEOPLE)
        parts = p["name"].split()
        fem = len(parts) > 2 and parts[2].endswith("на")
        txt = random.choice(POST_TEXTS).format(
            a="а" if fem else "", role=random.choice(ROLES), task=random.choice(TASKS),
            topic=random.choice(TOPICS), stuff=random.choice(STUFF),
            problem=random.choice(PROBLEMS), weeks=random.choice(WEEKS),
            ready=pr.get("readiness", "50"), money=money(random.randint(20, 900) * 1000))
        hours += random.choice([2, 5, 9, 20, 30, 48, 72, 120])
        d = 8 - min(30, hours // 24)
        date = f"2026-09-{d:02d}" if d >= 1 else "2026-08-" + f"{31 + d:02d}"
        label = (ago(hours, "час", "часа", "часов") if hours < 24 else
                 "вчера" if hours < 48 else ago(hours // 24, "день", "дня", "дней"))
        out.append("        { avatar: '%s', name: '%s', time: '%s', date: '%s', hoursAgo: %d, "
                   "text: '%s', likes: %d, comments: %d }"
                   % (p["avatar"], p["name"].replace("'", "\\'"), label, date, hours,
                      txt.replace("'", "\\'"), random.randint(0, 24), random.randint(0, 9)))
    return ",\n".join(out)


s = rd("feed.html")
m = re.search(r"var PROJECT_NEWS = \{", s)
depth, i = 1, m.end()
while depth:
    ch = s[i]
    depth += 1 if ch == "{" else -1 if ch == "}" else 0
    i += 1
end = i
old = s[m.end():end - 1]
keep = []
for key in ("printer3d", "greenhouse"):
    km = re.search(rf"\n    {key}: \{{", old)
    if km:
        d2, j = 1, km.end()
        while d2:
            d2 += 1 if old[j] == "{" else -1 if old[j] == "}" else 0
            j += 1
        keep.append(old[km.start():j].rstrip())

blocks = list(keep)
TRANSLIT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
            "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
            "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya", "-": "_"}

used_keys = set()
for pr in random.sample(PROJ, 28):
    # идентификаторы проектов бывают кириллическими; без транслитерации от них
    # оставались одни цифры и ключи выходили вида p_17 — нечитаемо в коде
    key = "".join(TRANSLIT.get(c, c if c.isalnum() and c.isascii() else "") for c in pr["id"].lower())
    key = re.sub(r"_+", "_", key).strip("_")[:28] or "proj"
    if key[:1].isdigit():
        key = "p_" + key
    if key in used_keys or any(f"\n    {key}: " in b for b in blocks):
        continue
    used_keys.add(key)
    blocks.append(
        "\n    %s: {\n      title: '%s',\n      link: 'project.html?id=%s',\n      image: '%s',\n"
        "      posts: [\n%s\n      ]\n    }"
        % (key, pr["title"].replace("'", "\\'"), pr["id"], pr.get("img", "images/photos/toolbox.jpg"),
           feed_posts(pr, random.randint(4, 6))))

s = s[:m.end()] + ",".join(blocks) + "\n  " + s[end - 1:]
wr("feed.html", s)
print(f"feed.html: проектов с новостями {len(blocks)}, постов {s.count('{ avatar:')}")

print("готово")
