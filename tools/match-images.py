# -*- coding: utf-8 -*-
"""Подбор фотографии к карточке по смыслу, а не по кругу.

Раздача картинок «по очереди» делает каталог пёстрым, но бессмысленным:
у проекта «Строительный 3D-принтер» оказывается библиотека, у теплицы — поле.
Здесь наоборот: из названия карточки достаются ключевые слова, по ним
подбирается тематическая фотография, и уже среди подходящих выбирается ещё
не занятая — так и по смыслу совпадает, и повторов на странице нет.

Если тема не распознана или все тематические фото заняты, берётся
следующая свободная из общего пула — но это запасной путь, а не основной.

Запуск:  python tools/match-images.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ключевое слово в названии карточки -> куски имён файлов, подходящих по теме
TOPICS = [
    (['цемент'], ['cement-bag']),
    (['свароч', 'сварк', 'сварщик'], ['welding-machine', 'welding-work', 'welder']),
    (['генератор', 'электростанц'], ['diesel-generator', 'solar-farm']),
    (['теплогенератор', 'сушилк'], ['herb-drying', 'grain-silo']),

    (['брус', 'доск', 'пиломатериал', 'вагонк', 'фанер'], ['timber-beam', 'wood-planks', 'sawmill-logs']),
    (['арматур', 'профиль', 'уголок', 'швеллер'], ['rebar-steel', 'metal-roof']),
    (['бетономешалк', 'миксер', 'бетоновоз'], ['concrete-mixer', 'concrete-truck']),
    (['кран', 'манипулятор', 'автокран'], ['crane-truck']),
    (['леса', 'подмост'], ['scaffolding']),
    (['инструмент', 'набор'], ['toolbox']),
    (['спецодежд', 'сиз', 'защит'], ['workwear-ppe']),
    (['морозильн', 'ларь', 'заморозк'], ['chest-freezer', 'cold-storage']),
    (['мясорубк', 'фарш', 'мясн'], ['meat-grinder', 'meat-band-saw', 'meat-processing']),
    (['тестораскат', 'тесто'], ['dough-sheeter-machine']),
    (['молоко', 'бутыл'], ['milk-bottles', 'milk-tank']),
    (['сахар'], ['sugar-white']),
    (['семен', 'посевн'], ['seed-bags']),
    (['ящик', 'коробк', 'тара'], ['potato-crate', 'vegbox-csa']),
    (['микрозайм', 'заём', 'финанс', 'деньг', 'касса'], ['finance-money']),
    (['видеонаблюден', 'камер', 'охран'], ['cctv-camera']),
    (['гараж', 'бокс'], ['garage-building']),
    (['офис', 'помещен', 'аренда помещ'], ['office-rent', 'office-desk']),
    (['велосипед', 'велокурьер'], ['cargo-bike', 'bicycle-repair']),
    (['микроавтобус', 'пассажир'], ['van-transfer', 'delivery-van']),
    (['дрон', 'бпла', 'квадрокоптер'], ['drone-agriculture']),
    (['рация', 'радиостанц'], ['radio-set']),
    (['обувь', 'сапог'], ['shoe-repair']),
    (['электромонт', 'электрик'], ['electrician', 'electric-panel']),
    (['каменщик', 'кладк'], ['mason', 'brick']),
    (['сварщик'], ['welder', 'welding']),
    (['программист', 'разработчик'], ['programmer', 'coding']),
    (['бухгалтер', 'учёт'], ['accountant', 'office-desk']),
    (['юрист', 'правов'], ['lawyer']),
    (['автомеханик', 'автослесар'], ['car-mechanic', 'car-service']),
    (['дизайнер интерьер'], ['interior-designer']),
    (['веб-дизайн', 'дизайнер'], ['web-designer', 'interior-designer']),
    (['сантехник', 'водоснабж'], ['plumber']),
    (['столяр', 'плотник'], ['carpenter', 'carpentry']),
    (['швея', 'портн', 'пошив'], ['seamstress', 'sewing']),
    (['флорист', 'цвет'], ['florist']),
    (['фотограф', 'съёмк'], ['photographer']),
    (['логист'], ['logistician', 'delivery-van']),
    (['маркетолог', 'реклам'], ['marketer']),
    (['кондитер', 'выпечк'], ['pastry-chef', 'bakery']),
    (['гравиров'], ['engraver']),
    (['пчеловод'], ['beekeeper', 'apiary']),
    (['теплиц', 'парник', 'овощ', 'зелен', 'рассад'], ['greenhouse', 'vegetable', 'nursery-seedlings', 'tomato']),
    (['пекарн', 'хлеб', 'выпечк', 'булоч'], ['bakery', 'bread', 'flour-mill']),
    (['сыр', 'молок', 'молоч', 'доил', 'доярк'], ['cheese', 'milk', 'dairy', 'cattle-barn']),
    (['пасек', 'мёд', 'мед ', 'пчел', 'улей', 'улья'], ['apiary', 'honey', 'bee']),
    (['овц', 'шерст', 'баран', 'отар'], ['sheep', 'wool']),
    (['коз'], ['goat', 'sheep']),
    (['птиц', 'кур', 'яйц', 'инкубат'], ['poultry', 'chicken']),
    (['рыб', 'пруд', 'форел'], ['fish']),
    (['солнечн', 'панел', 'энерг', 'ветр', 'ветряк', 'зарядн'], ['solar', 'wind-turbine', 'electric-panel']),
    (['3d', '3д', 'принтер', 'чпу', 'станок'], ['printer3d', 'cnc', '3d-printing']),
    (['мусор', 'переработк', 'вторсыр', 'пластик', 'компост'], ['recycling', 'plastic', 'compost']),
    (['библиотек', 'книг'], ['library']),
    (['мост'], ['bridge']),
    (['площадк', 'детск', 'сад '], ['playground', 'kindergarten']),
    (['дом', 'жиль', 'модульн', 'сруб', 'брус', 'кровл', 'крыш'], ['house', 'roof', 'modular', 'metal-roof', 'timber']),
    (['кирпич', 'кладк', 'стен', 'фасад'], ['brick', 'building-renovation', 'concrete']),
    (['бетон', 'фундамент', 'стяжк'], ['concrete', 'cement']),
    (['экскават', 'трактор', 'техник', 'погрузчик', 'мтз'], ['excavator', 'tractor', 'mini-tractor', 'crane-truck']),
    (['зерн', 'мельниц', 'мук', 'ячмен', 'пшениц'], ['grain', 'flour', 'wheat', 'combine-harvester']),
    (['картоф', 'морков', 'лук', 'корнеплод'], ['potato', 'carrot', 'onion', 'vegetable']),
    (['ягод', 'сад', 'яблон', 'саженц'], ['berry', 'apple-orchard', 'nursery-seedlings']),
    (['гриб'], ['mushroom']),
    (['склад', 'хранилищ', 'холодильн', 'ангар'], ['warehouse', 'cold-storage', 'chest-freezer', 'garage']),
    (['мастерск', 'ремесл', 'столяр', 'плотник', 'дерев'], ['craft-workshop', 'carpentry', 'makerspace', 'sawmill']),
    (['кузн', 'ковк', 'металл', 'сварк'], ['blacksmith', 'welding', 'metal']),
    (['гончар', 'керамик', 'глин'], ['pottery']),
    (['ткац', 'ткач', 'пошив', 'шве', 'одежд'], ['weaving', 'sewing', 'textile']),
    (['прачечн', 'стирк'], ['laundry', 'laundromat']),
    (['коворкинг', 'офис'], ['coworking', 'office-desk', 'laptop-desk']),
    (['медпункт', 'клиник', 'здоров', 'фельдшер', 'ветерин'], ['clinic', 'medical']),
    (['бан', 'сауна'], ['sauna', 'banya']),
    (['магазин', 'лавк', 'рынок', 'ярмарк', 'сбыт', 'торгов'], ['market', 'shop']),
    (['мясн', 'мясо', 'пельмен', 'колбас', 'свинин', 'говядин'], ['pelmeni', 'meat', 'pork', 'beef', 'butcher']),
    (['мёдов', 'варень', 'консерв', 'заготовк'], ['canning', 'honey-jar']),
    (['трав', 'сушк', 'сушил'], ['herb-drying', 'grain-silo']),
    (['crm', 'ит', 'софт', 'программ', 'сайт', 'приложен', 'цифров', 'данных', 'сервер'], ['open-source-crm', 'programmer', 'laptop-desk', 'server-rack', 'coding']),
    (['обучен', 'курс', 'школ', 'образован', 'лекц'], ['classroom', 'coding-class', 'library']),
    (['дорог', 'асфальт', 'тротуар'], ['road-repair', 'bridge']),
    (['перевоз', 'логистик', 'достав', 'фургон', 'автопарк', 'транспорт'], ['delivery-van', 'cargo-truck', 'car-rental', 'cargo-bike']),
    (['музей', 'реставрац', 'историч'], ['historic-restoration', 'museum']),
    (['кемпинг', 'турист', 'гостев', 'палатк'], ['camping', 'guest-house']),
    (['спорт', 'площадка', 'скалодром'], ['sport-ground', 'climbing-gym']),
    (['собран', 'сообществ', 'встреч', 'клуб'], ['community-meeting', 'business-meeting']),
    (['генератор', 'котельн', 'отоплен'], ['diesel-generator', 'boiler-room']),
    (['утеплит', 'изоляц', 'вата'], ['mineral-wool']),
    (['фаблаб', 'fablab', 'антикафе', 'коллективн'], ['makerspace', 'craft-workshop']),
    (['дом культуры', 'клуб', 'обществен'], ['community-meeting', 'business-meeting']),
    (['ферм', 'хозяйств', 'скотн'], ['cattle-barn', 'goat-farm', 'poultry-house']),
    (['пункт приёма', 'приём'], ['recycling-plastic', 'plastic-recycling']),
    (['вода', 'скважин', 'колодец', 'водоснабжен'], ['water-well']),
    (['сеть', 'интернет', 'связь'], ['server-rack', 'radio-set']),
    (['ремонт'], ['building-renovation', 'car-service', 'bicycle-repair']),
    (['аренд', 'прокат'], ['car-rental', 'warehouse-shelves']),
    (['офисн', 'бумаг', 'печат'], ['mfu-printer', 'office-desk']),
    (['земл', 'участок', 'пастбищ', 'сенокос', 'сено', 'корм'], ['land-plot', 'hay-bales', 'pasture', 'meadow']),
]

GENERIC_LAST = ['business-meeting', 'coworking', 'office-desk', 'craft-workshop']


def photos():
    d = os.path.join(ROOT, 'images', 'photos')
    return ['images/photos/' + f for f in sorted(os.listdir(d)) if f.lower().endswith(('.jpg', '.png'))]


ALL = photos()


def tokens(path):
    """Имя файла разбираем на слова: house не должен ловить greenhouse."""
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    return stem.split('-')


def matches(path, part):
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    if '-' in part:                      # шаблон из двух слов сверяем с именем целиком
        return stem == part or stem.startswith(part)
    toks = tokens(path)
    return any(tok == part or (len(part) > 4 and tok.startswith(part)) for tok in toks)


def candidates(title, pool=None):
    """Совпадения сортируем по длине ключевого слова: в «Пельменях домашней
       лепки» слово «пельмен» точнее, чем «дом», иначе к пельменям приедет дом."""
    t = title.lower()
    files = pool if pool is not None else ALL
    groups = []
    for words, parts in TOPICS:
        best = max((len(w) for w in words if w in t), default=0)
        if best:
            groups.append((best, parts))
    groups.sort(key=lambda g: -g[0])
    hits = []
    for _, parts in groups:
        for p in parts:
            hits += [f for f in files if matches(f, p)]
    seen, out = set(), []
    for f in hits:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def assign(page, card_re, img_re, title_re, pool=None):
    """Правило простое: фото должно подходить по смыслу и не повторяться в
       пределах страницы. Страница показывает 20 карточек, поэтому одно и то
       же фото разрешено использовать снова не раньше, чем через 24 карточки —
       в поле зрения повторов нет, а тематичность не приносится в жертву."""
    GAP = 24
    s = io.open(os.path.join(ROOT, page), encoding='utf-8').read()
    last = {}
    idx = {'n': 0}
    files = pool if pool is not None else ALL
    spare = [f for f in files if not any(g in f for g in GENERIC_LAST)] +             [f for f in files if any(g in f for g in GENERIC_LAST)]
    stats = {'topic': 0, 'spare': 0}

    def free(f, i):
        return (i - last.get(f, -10 ** 6)) >= GAP

    def fix(m):
        card = m.group(0)
        i = idx['n']
        idx['n'] += 1
        t = re.search(title_re, card)
        title = re.sub(r'<[^>]+>', '', t.group(1)).strip() if t else ''
        pick = None
        for f in candidates(title, files):
            if free(f, i):
                pick, kind = f, 'topic'
                break
        if not pick:
            for f in spare:
                if free(f, i):
                    pick, kind = f, 'spare'
                    break
        if not pick:
            pick, kind = spare[i % len(spare)], 'spare'
        stats[kind] += 1
        last[pick] = i
        card = re.sub(img_re, lambda im: im.group(1) + pick + im.group(3), card, count=1)
        if title:
            card = re.sub(r'(<img[^>]*\salt=")[^"]*(")',
                          lambda a: a.group(1) + title + a.group(2), card, count=1)
        return card

    s2 = re.sub(card_re, fix, s, flags=re.S)
    io.open(os.path.join(ROOT, page), 'w', encoding='utf-8', newline='').write(s2)
    print('%-22s по теме %3d, из общего запаса %3d' % (page, stats['topic'], stats['spare']))


def main():
    assign('projects.html', r'<a class="ptile".*?</a>', r'(src=")(images/[^"]+)(")',
           r'<div class="pname">([^<]*)')
    assign('resources.html', r'<a class="ptile".*?</a>', r'(src=")(images/[^"]+)(")',
           r'<div class="pname">([^<]*)')
    skills_pool = ['images/skills/' + f for f in sorted(os.listdir(os.path.join(ROOT, 'images', 'skills')))
                   if f.lower().endswith(('.jpg', '.png'))] + ALL
    assign('skills.html', r'<a class="vacancy-card".*?</a>', r'(src=")(images/(?!avatars)[^"]+)(")',
           r'<div class="vacancy-title">([^<]*)', pool=skills_pool)
    assign('nma-catalog.html', r'<a class="vacancy-card".*?</a>', r'(src=")(images/[^"]+)(")',
           r'<div class="vacancy-title">([^<]*)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
