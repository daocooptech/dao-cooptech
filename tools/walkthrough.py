# -*- coding: utf-8 -*-
"""Сплошной проход по сайту: то, что не ловит tools/check.py.

check.py следит за целостностью — ссылки, теги, шапка. Этот скрипт смотрит на
содержание: не осталось ли заглушек, не вылезли ли на экран запрещённые слова,
достижимы ли страницы из навигации, единообразны ли термины.

Запуск:  python tools/walkthrough.py
"""
import re, io, os, json, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PAGES = sorted(glob.glob("*.html"))


def rd(p):
    return io.open(p, encoding="utf-8").read()


def visible(s):
    """Текст, который видит человек: без скриптов, стилей и разметки."""
    s = re.sub(r"<script\b.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s)


issues = collections.defaultdict(list)

# 1. слова, которых не должно быть на экране (prototype-conventions)
BANNED = {
    "узел": r"\bузл[аеоу]?в?\b|\bузел\b", "реплика": r"\bреплик[аиуой]\b",
    "синхронизация": r"\bсинхронизаци[ияюей]\b", "федерация": r"\bфедерац[ияиюей]\b",
    "консенсус": r"\bконсенсус\w*\b", "хэш": r"\bхэш\w*\b|\bхеш\w*\b",
    "подпись ключом": r"подпис\w+ ключом",
}
# «Узел связи» — здание, «узел подачи смеси» — часть машины. Это обычные русские
# слова, а запрет касается технического жаргона платформы. Без этого списка
# проверка кричит на исправный текст, и на неё перестают смотреть.
SAFE = [r"узел связи", r"узла связи", r"узел подачи", r"узла подачи",
        r"узел учёта", r"узел ввода", r"тепловой узел"]
for p in PAGES:
    v = visible(rd(p))
    for name, rx in BANNED.items():
        real = [m for m in re.finditer(rx, v, re.I)
                if not any(re.match(sx, v[m.start():m.start() + 30], re.I) for sx in SAFE)]
        if real:
            m = real[0]
            ctx = v[max(0, m.start() - 45):m.end() + 45].strip()
            issues["Запрещённые на экране слова"].append(f"{p}: «{name}» ×{len(real)} — …{ctx}…")

# 2. заглушки и следы недоделок
# «поправить под себя» и «не макеты-заглушки» — нормальный текст интерфейса,
# поэтому ищем сами следы недоделки, а не любое употребление слова
STUBS = [r"\bLorem ipsum\b", r"\bTODO\b", r"\bFIXME\b", r"\bпример текста",
         r"\bтекст текст", r"\bxxx\b", r"\bздесь будет\b", r"\bнужно дописать\b"]
for p in PAGES:
    v = visible(rd(p))
    for rx in STUBS:
        if re.search(rx, v, re.I):
            m = re.search(rx, v, re.I)
            issues["Следы недоделок в тексте"].append(
                f"{p}: …{v[max(0, m.start()-40):m.end()+40].strip()}…")

# 3. заголовки
for p in PAGES:
    s = rd(p)
    h1 = re.findall(r"<h1\b[^>]*>(.*?)</h1>", s, re.S)
    if len(h1) == 0:
        issues["Нет <h1>"].append(p)
    elif len(h1) > 1:
        issues["Больше одного <h1>"].append(f"{p}: {len(h1)}")
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    if not t or not t.group(1).strip():
        issues["Пустой <title>"].append(p)
    else:
        title = t.group(1).strip()
        # лендинг подписан полным названием, портал контрагента — номером сделки:
        # и то и другое осознанно, имя платформы там не нужно
        named = "cooptech" in title.lower() or "КООПТЕХ" in title
        if not named and p not in ("portal.html",):
            issues["<title> без имени платформы"].append(f"{p}: {title[:50]}")

# 4. достижимость: на какие страницы никто не ссылается
linked = set()
for p in PAGES:
    for m in re.finditer(r'href="([^"#?]+\.html)', rd(p)):
        linked.add(m.group(1))
orphans = [p for p in PAGES if p not in linked and p != "index.html"]
for p in orphans:
    issues["Страницы, на которые никто не ссылается"].append(p)

# 5. единство терминов
TERMS = {
    "Кошелёк/Кошелек": (r"Кошелек\b", "пишем «Кошелёк» через ё"),
    "ё в «её»": (r"\bее\b", "пишем «её»"),
    "оргсбор/орг. сбор": (r"орг\.\s?сбор", "пишем «оргсбор» одним словом"),
    "ЦФА строчными": (r"\bцфа\b", "аббревиатура пишется прописными"),
}
for p in PAGES:
    v = visible(rd(p))
    for name, (rx, why) in TERMS.items():
        n = len(re.findall(rx, v))
        if n:
            issues["Единство терминов"].append(f"{p}: {name} ×{n} — {why}")

# 6. документация против кода
DOCS = sorted(glob.glob("docs/*.md"))
for d in DOCS:
    t = rd(d)
    for m in re.finditer(r"`([a-z0-9\-]+\.html)`", t):
        if not os.path.exists(m.group(1)):
            issues["Документация ссылается на несуществующую страницу"].append(f"{d}: {m.group(1)}")
    for m in re.finditer(r"`(tools/[a-z0-9\-_]+\.py)`", t):
        if not os.path.exists(m.group(1)):
            issues["Документация ссылается на несуществующий скрипт"].append(f"{d}: {m.group(1)}")

print(f"страниц: {len(PAGES)}, документов: {len(DOCS)}\n")
total = 0
for kind, items in issues.items():
    total += len(items)
    print(f"── {kind} — {len(items)}")
    for it in items[:12]:
        print(f"     {it}")
    if len(items) > 12:
        print(f"     … и ещё {len(items) - 12}")
    print()
print(f"всего замечаний: {total}")
