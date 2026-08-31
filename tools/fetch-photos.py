# -*- coding: utf-8 -*-
"""Догрузка тематических фотографий с Викисклада.

Источник тот же, что использовался в проекте раньше: Wikimedia Commons —
свободные лицензии и открытый API без ключа. Скрипт ищет по ключевому слову,
берёт первую подходящую фотографию и кладёт её в images/photos под понятным
именем. Уже скачанные файлы не перекачиваются.

Запуск:  python tools/fetch-photos.py
"""
import io
import json
import os
import time
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'images', 'photos')
API = 'https://commons.wikimedia.org/w/api.php'
UA = 'DAO-COOPTECH-prototype/1.0 (educational prototype; contact via github.com/daocooptech)'

# имя файла -> поисковый запрос на Викискладе
WANTED = [
    ('apiary-hives', 'apiary beehives'),
    ('cheese-making', 'cheese making dairy'),
    ('sheep-flock', 'sheep flock pasture'),
    ('goat-farm', 'goat farm'),
    ('cattle-barn', 'cattle barn cows'),
    ('tractor-field', 'tractor ploughing field'),
    ('combine-harvester', 'combine harvester wheat'),
    ('grain-silo', 'grain silo storage'),
    ('vegetable-garden', 'vegetable garden beds'),
    ('apple-orchard', 'apple orchard trees'),
    ('berry-harvest', 'berry harvest basket'),
    ('mushroom-farm', 'mushroom cultivation'),
    ('fish-pond', 'fish pond aquaculture'),
    ('poultry-house', 'poultry chicken house'),
    ('greenhouse-tomato', 'greenhouse tomato plants'),
    ('hay-bales', 'hay bales field'),
    ('sawmill-logs', 'sawmill logs timber'),
    ('carpentry-shop', 'carpentry workshop wood'),
    ('blacksmith-forge', 'blacksmith forge anvil'),
    ('pottery-wheel', 'pottery wheel clay'),
    ('weaving-loom', 'weaving loom textile'),
    ('sewing-workshop', 'sewing workshop tailor'),
    ('shoe-repair', 'shoe repair cobbler'),
    ('bicycle-repair', 'bicycle repair shop'),
    ('car-service', 'car repair garage service'),
    ('welding-work', 'welding metal work'),
    ('cnc-machine', 'cnc milling machine'),
    ('3d-printing', '3d printer printing'),
    ('solar-panels', 'solar panels roof'),
    ('wind-turbine', 'wind turbine farm'),
    ('water-well', 'water well village'),
    ('boiler-room', 'boiler room heating'),
    ('electric-panel', 'electrical panel switchboard'),
    ('road-repair', 'road repair asphalt'),
    ('bridge-construction', 'bridge construction site'),
    ('house-frame', 'timber frame house construction'),
    ('roof-work', 'roof construction workers'),
    ('brick-wall', 'bricklaying wall construction'),
    ('concrete-pour', 'concrete pouring construction'),
    ('excavator-work', 'excavator digging'),
    ('warehouse-shelves', 'warehouse shelves storage'),
    ('cold-storage', 'cold storage refrigerated warehouse'),
    ('delivery-van', 'delivery van cargo'),
    ('cargo-truck', 'cargo truck lorry'),
    ('farmers-market', 'farmers market stall'),
    ('village-shop', 'village grocery shop'),
    ('bakery-bread', 'bakery bread loaves'),
    ('flour-mill', 'flour mill grain'),
    ('honey-extraction', 'honey extraction beekeeper'),
    ('milk-tank', 'milk tank dairy farm'),
    ('meat-shop', 'butcher shop meat'),
    ('canning-jars', 'canning jars preserves'),
    ('herb-drying', 'herb drying rack'),
    ('seed-bags', 'seed bags agriculture'),
    ('community-meeting', 'community meeting village hall'),
    ('classroom-training', 'classroom training adults'),
    ('library-books', 'library bookshelves'),
    ('kindergarten-play', 'kindergarten playground children'),
    ('medical-office', 'medical office rural clinic'),
    ('sport-ground', 'sport ground village'),
    ('camping-site', 'camping site tents'),
    ('guest-house', 'guest house rural'),
    ('sauna-banya', 'russian banya sauna'),
    ('laundry-machines', 'laundromat washing machines'),
    ('office-desk', 'office desk workplace'),
    ('server-rack', 'server rack datacenter'),
    ('drone-agriculture', 'agricultural drone field'),
    ('recycling-plastic', 'plastic recycling facility'),
    ('compost-heap', 'compost heap organic'),
    ('nursery-seedlings', 'plant nursery seedlings'),
]


def api(params):
    """Викисклад отдаёт 429 при частых запросах — идём медленно и с повторами."""
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(4):
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))
            time.sleep(3.0)
            return data
        except Exception:
            time.sleep(8 * (attempt + 1))
    raise RuntimeError('rate limit')


def find_image(query):
    data = api({
        'action': 'query', 'format': 'json', 'generator': 'search',
        'gsrsearch': 'filetype:bitmap ' + query, 'gsrnamespace': '6', 'gsrlimit': '6',
        'prop': 'imageinfo', 'iiprop': 'url|mime', 'iiurlwidth': '720',
    })
    pages = (data.get('query') or {}).get('pages') or {}
    for page in pages.values():
        info = (page.get('imageinfo') or [{}])[0]
        mime = info.get('mime', '')
        url = info.get('thumburl') or info.get('url')
        if url and mime in ('image/jpeg', 'image/png'):
            return url
    return None


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    added, skipped, failed = 0, 0, []
    for name, query in WANTED:
        path = os.path.join(OUT, name + '.jpg')
        if os.path.exists(path):
            skipped += 1
            continue
        try:
            url = find_image(query)
            if not url:
                failed.append(name)
                continue
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            data = urllib.request.urlopen(req, timeout=60).read()
            time.sleep(2.0)
            if len(data) < 3000:
                failed.append(name)
                continue
            io.open(path, 'wb').write(data)
            added += 1
        except Exception as exc:            # сеть или отсутствующий файл — не повод падать
            failed.append('%s (%s)' % (name, str(exc)[:40]))
    print('скачано: %d, уже было: %d, не нашлось: %d' % (added, skipped, len(failed)))
    if failed:
        print('не получилось:', ', '.join(failed[:12]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
