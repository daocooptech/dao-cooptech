# -*- coding: utf-8 -*-
"""Синхронизация общей шапки и сайдбара по всем страницам прототипа.

Зачем: раньше шапка + меню были скопированы в 58 HTML-файлов, и копии успели
разойтись — было 8 разных вариантов одного и того же блока. Теперь эталон один
(tools/shell.html), а этот скрипт разносит его по страницам.

Как пользоваться:
    python tools/sync-shell.py            # разнести эталон по страницам
    python tools/sync-shell.py --check    # только проверить, ничего не писать

Правишь меню — правишь tools/shell.html и запускаешь скрипт, а не 58 файлов.

Какой пункт меню подсвечен на какой странице — в tools/_active.json
(страница -> href пункта). Добавил новую страницу — допиши её туда;
если страницы там нет, активный пункт просто не подсвечивается.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHELL_RE = re.compile(r'<header class="topbar">.*?</aside>', re.S)

# Страницы для неавторизованного посетителя: у них своя шапка без сайдбара,
# поиска и кнопки «выйти» (эталон — tools/shell-public.html).
PUBLIC_RE = re.compile(r'<header class="public-header">.*?</header>', re.S)
PUBLIC = {'index.html', 'login.html', 'registration.html', 'password-recovery.html', 'portal.html'}
SKIP = set()


def read(path):
    return io.open(path, encoding='utf-8').read()


def build_shell(template, active_href):
    """Подставить class="active" тому пункту меню, который ведёт на active_href."""
    if not active_href:
        return template
    pattern = '<a href="%s"' % active_href
    if pattern not in template:
        sys.stderr.write('  ! в эталоне нет пункта %s\n' % active_href)
        return template
    return template.replace(pattern, pattern + ' class="active"', 1)


def main():
    check_only = '--check' in sys.argv
    template = read(os.path.join(ROOT, 'tools', 'shell.html')).rstrip('\n')
    public = read(os.path.join(ROOT, 'tools', 'shell-public.html')).rstrip('\n')
    active = json.loads(read(os.path.join(ROOT, 'tools', '_active.json')))

    changed, skipped, missing = [], [], []
    for name in sorted(os.listdir(ROOT)):
        if not name.endswith('.html') or name in SKIP:
            continue
        path = os.path.join(ROOT, name)
        page = read(path)
        if name in PUBLIC:
            if not PUBLIC_RE.search(page):
                missing.append(name)
                continue
            new = PUBLIC_RE.sub(lambda _m: public, page, count=1)
            if new == page:
                skipped.append(name)
            else:
                changed.append(name)
                if not check_only:
                    io.open(path, 'w', encoding='utf-8', newline='').write(new)
            continue
        if not SHELL_RE.search(page):
            missing.append(name)
            continue
        shell = build_shell(template, active.get(name))
        new = SHELL_RE.sub(lambda _m: shell, page, count=1)
        if new == page:
            skipped.append(name)
            continue
        changed.append(name)
        if not check_only:
            io.open(path, 'w', encoding='utf-8', newline='').write(new)

    verb = 'разошлись с эталоном' if check_only else 'обновлено'
    print('%s: %d' % (verb, len(changed)))
    for n in changed:
        print('   ', n)
    print('уже совпадали: %d' % len(skipped))
    if missing:
        print('без блока шапки (пропущены): %s' % ', '.join(missing))
    if check_only and changed:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
