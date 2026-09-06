# -*- coding: utf-8 -*-
"""Сплошная проверка прототипа ДАО КООПТЕХ.

Одна команда вместо ручного осмотра семидесяти страниц. Проверяет то, что
ломается тихо и обнаруживается через неделю:

  1. Битые локальные ссылки и картинки.
  2. Баланс <div> на каждой странице.
  3. Расхождение шапки и сайдбара с эталоном (tools/sync-shell.py --check).
  4. Страницы, не прописанные в tools/_active.json.
  5. Внешние ссылки на CDN — их в прототипе быть не должно, ресурсы локальные.

Запуск:  python tools/check.py           — проверить всё
         python tools/check.py --quiet   — только итог и ошибки
Код возврата 1, если что-то найдено, — годится для хука и для CI.
"""
import io, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUIET = "--quiet" in sys.argv
os.chdir(ROOT)

PAGES = sorted(f for f in os.listdir(".") if f.endswith(".html"))
LINK = re.compile(r'(?:href|src)="([^"]+)"')
# внутри JS ссылки собираются конкатенацией — это не разметка, а код
JS_ARTIFACT = ("' +", '" +', "${", "+ ", "'+", '"+')
CDN = re.compile(r'(?:href|src)="https?://(?!localhost)([^/"]+)')

problems = {}


def add(kind, msg):
    problems.setdefault(kind, []).append(msg)


def say(*a):
    if not QUIET:
        print(*a)


# 1. ссылки и картинки -------------------------------------------------------
for page in PAGES:
    s = io.open(page, encoding="utf-8").read()
    for m in LINK.finditer(s):
        t = m.group(1)
        if any(x in t for x in JS_ARTIFACT):
            continue
        t = t.split("#")[0].split("?")[0]
        if not t or t.startswith(("http", "//", "mailto:", "tel:", "data:", "javascript:")):
            continue
        if not os.path.exists(t):
            add("Битые локальные ссылки", f"{page} → {t}")

# 2. баланс div --------------------------------------------------------------
for page in PAGES:
    s = io.open(page, encoding="utf-8").read()
    s = re.sub(r"<script\b.*?</script>", "", s, flags=re.S | re.I)
    op = len(re.findall(r"<div\b", s, re.I))
    cl = len(re.findall(r"</div>", s, re.I))
    if op != cl:
        add("Разбалансированные <div>", f"{page}: открыто {op}, закрыто {cl}")

# 3. шапка и сайдбар ---------------------------------------------------------
try:
    r = subprocess.run([sys.executable, "tools/sync-shell.py", "--check"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        add("Шапка/сайдбар разошлись с эталоном",
            (r.stdout or "") .strip().splitlines()[-1] if r.stdout else "sync-shell вернул ошибку")
except Exception as e:
    add("Шапка/сайдбар: проверка не запустилась", str(e))

# 4. страницы вне _active.json ----------------------------------------------
# Публичные страницы (лендинг, вход, регистрация, восстановление) идут без
# сайдбара, подсвечивать в меню у них нечего. Список берём из самого
# sync-shell.py, чтобы он не разъезжался с проверкой.
def public_pages():
    try:
        src = io.open("tools/sync-shell.py", encoding="utf-8").read()
        m = re.search(r"^PUBLIC\s*=\s*\{(.+?)\}", src, re.M | re.S)
        return set(re.findall(r"['\"]([^'\"]+\.html)['\"]", m.group(1))) if m else set()
    except Exception:
        return set()


try:
    active = json.load(io.open("tools/_active.json", encoding="utf-8"))
    known = set(active) if isinstance(active, dict) else set(active)
    skip = public_pages()
    for page in PAGES:
        if page not in known and page not in skip:
            add("Страницы без записи в tools/_active.json", page)
except Exception as e:
    add("tools/_active.json не прочитан", str(e))

# 5. внешние ресурсы ---------------------------------------------------------
for page in PAGES:
    s = io.open(page, encoding="utf-8").read()
    for m in CDN.finditer(s):
        add("Внешние ресурсы (должно быть локально)", f"{page} → {m.group(1)}")

# итог -----------------------------------------------------------------------
total = sum(len(v) for v in problems.values())
say(f"Проверено страниц: {len(PAGES)}")
for kind, items in problems.items():
    print(f"\n{kind} — {len(items)}:")
    for it in items[:25]:
        print(f"   {it}")
    if len(items) > 25:
        print(f"   … и ещё {len(items) - 25}")

if total == 0:
    print(f"\nЧисто: {len(PAGES)} страниц, замечаний нет.")
    sys.exit(0)
print(f"\nВсего замечаний: {total}")
sys.exit(1)
