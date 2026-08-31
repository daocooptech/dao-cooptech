# -*- coding: utf-8 -*-
"""Раздача ЛИЦ и ЛОГОТИПОВ по каталогам без повторов на странице.

Тематические фотографии (проекты, ресурсы, навыки, НМА) раздаёт другой
скрипт — tools/match-images.py: там картинка подбирается по смыслу названия.
Здесь только то, что смыслу карточки не противоречит: аватары людей и
логотипы организаций.

После генерации карточек одно и то же фото встречалось по десятку раз —
каталог выглядел как размноженная копия. Скрипт проходит по карточкам в
порядке документа и выдаёт каждой следующую картинку из пула по кругу.

Пул перемешивается детерминированно (фиксированное зерно), поэтому повторный
запуск даёт тот же результат, а разные каталоги получают разный порядок —
одна и та же фотография не оказывается на одинаковых местах в разных
разделах. Если карточек больше, чем картинок, повтор наступает не раньше,
чем через размер пула — а страница показывает 20 объектов, поэтому в поле
зрения одинаковых картинок не будет.

Запуск:  python tools/spread-images.py
"""
import io
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pool(folder, exts=('.jpg', '.jpeg', '.png')):
    path = os.path.join(ROOT, *folder.split('/'))
    if not os.path.isdir(path):
        return []
    files = sorted(f for f in os.listdir(path) if f.lower().endswith(exts))
    return ['%s/%s' % (folder, f) for f in files]


def shuffled(items, seed):
    out = list(items)
    random.Random(seed).shuffle(out)
    return out


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, s):
    io.open(os.path.join(ROOT, p), 'w', encoding='utf-8', newline='').write(s)


def spread(page, card_re, img_re, images, title_re=None, seed=1):
    """Пройти по карточкам страницы и заменить путь к картинке на свой."""
    if not images:
        print('%-22s пул пуст' % page)
        return
    s = read(page)
    imgs = shuffled(images, seed)
    counter = {'i': 0, 'done': 0}

    def fix_card(m):
        card = m.group(0)
        title = ''
        if title_re:
            t = re.search(title_re, card)
            if t:
                title = re.sub(r'<[^>]+>', '', t.group(1)).strip()

        def fix_img(im):
            src = imgs[counter['i'] % len(imgs)]
            counter['i'] += 1
            counter['done'] += 1
            return im.group(1) + src + im.group(3)

        card2 = re.sub(img_re, fix_img, card, count=1)
        if title:
            card2 = re.sub(r'(<img[^>]*\salt=")[^"]*(")',
                           lambda a: a.group(1) + title + a.group(2), card2, count=1)
        return card2

    s2 = re.sub(card_re, fix_card, s, flags=re.S)
    write(page, s2)
    uniq = len(set(re.findall(img_re.replace('(', '(?:').replace('(?:?', '('), s2))) if False else None
    print('%-22s картинок заменено %3d, пул %3d' % (page, counter['done'], len(imgs)))


AVATARS = pool('images/avatars')
PHOTOS = pool('images/photos')
SKILLS = pool('images/skills') + PHOTOS
LOGOS = pool('img/org-logos', exts=('.png', '.jpg', '.svg'))


def main():
    # люди: аватар в карточке
    spread('people.html', r'<a class="vacancy-card".*?</a>',
           r'(src=")(images/avatars/[^"]+)(")', AVATARS,
           title_re=r'<div class="vacancy-title">([^<]*)', seed=11)

    # навыки: аватар владельца (фото ремесла — в match-images.py)
    spread('skills.html', r'<a class="vacancy-card".*?</a>',
           r'(src=")(images/avatars/[^"]+)(")', AVATARS, seed=33)

    # вакансии: аватар публикатора
    spread('vacancies.html', r'<a class="vacancy-card".*?</a>',
           r'(src=")(images/avatars/[^"]+)(")', AVATARS, seed=44)

    # организации: логотипы
    spread('organizations.html', r'<a class="ptile".*?</a>',
           r'(src=")(img/org-logos/[^"]+)(")', LOGOS,
           title_re=r'<div class="pname">([^<]*)', seed=77)

    # сделки: аватар контрагента там, где он фотографией
    spread('deals.html', r'<article class="deal-card".*?</article>',
           r'(src=")(images/avatars/[^"]+)(")', AVATARS, seed=99)
    return 0


if __name__ == '__main__':
    sys.exit(main())
