# -*- coding: utf-8 -*-
"""Наполнение каталогов прототипа до 100 карточек.

Карточки не пишутся с нуля: скрипт клонирует уже существующие в файле и
подставляет в копию другие имя, город, числа и уникальный id избранного.
Так разметка гарантированно остаётся валидной, фотографии берутся из тех,
что уже лежат в репозитории, а фильтры продолжают работать — data-атрибуты
меняются согласованно с видимым текстом.

Запуск:  python tools/fill-catalogs.py
Скрипт идемпотентен по количеству: доводит каждый каталог ровно до TARGET.
"""
import io
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = 100
random.seed(2026)

CITIES = ['Архангельск', 'Владивосток', 'Волгоград', 'Вологда', 'Воронеж', 'Дербент',
          'Екатеринбург', 'Ишим', 'Казань', 'Калининград', 'Кемерово', 'Краснодар',
          'Красноярск', 'Магнитогорск', 'Москва', 'Нижний Новгород', 'Нижний Тагил',
          'Новосибирск', 'Омск', 'Пермь', 'Ростов-на-Дону', 'Самара',
          'Санкт-Петербург', 'Сочи', 'Тобольск', 'Тюмень', 'Уфа', 'Хабаровск',
          'Челябинск', 'Ярославль']

SURNAMES_M = ['Ковалёв', 'Зайцев', 'Морозов', 'Лебедев', 'Никитин', 'Соколов', 'Гусев',
              'Беляев', 'Тарасов', 'Фомин', 'Орлов', 'Киселёв', 'Макаров', 'Логинов',
              'Дьяков', 'Шестаков', 'Ильин', 'Панов', 'Родионов', 'Юдин', 'Мельник',
              'Савельев', 'Ефимов', 'Комаров', 'Рябов', 'Носов', 'Щербаков', 'Токарев']
NAMES_M = ['Алексей', 'Пётр', 'Игорь', 'Сергей', 'Михаил', 'Андрей', 'Дмитрий', 'Николай',
           'Владимир', 'Артём', 'Роман', 'Егор', 'Виктор', 'Тимур', 'Юрий', 'Илья']
PATR_M = ['Иванович', 'Петрович', 'Сергеевич', 'Николаевич', 'Андреевич', 'Дмитриевич',
          'Алексеевич', 'Михайлович', 'Викторович', 'Юрьевич']
NAMES_F = ['Мария', 'Ольга', 'Елена', 'Анна', 'Татьяна', 'Ирина', 'Наталья', 'Светлана',
           'Екатерина', 'Юлия', 'Полина', 'Дарья', 'Ксения', 'Вера']
PATR_F = ['Ивановна', 'Петровна', 'Сергеевна', 'Николаевна', 'Андреевна', 'Дмитриевна',
          'Алексеевна', 'Михайловна', 'Викторовна', 'Юрьевна']

COOP_WORDS = ['Шукты', 'Взаимопомощь', 'СветСвои', 'Речной порт', 'Гостевой двор', 'Заря',
              'Колос', 'Северный лён', 'Тёплый край', 'Сыродел', 'Пчела', 'Гончар',
              'Лесное', 'Родник', 'Артель', 'Молочный путь', 'Сад', 'Пасека', 'Ткач',
              'Кузница', 'Плотник', 'Зерно', 'Овчина', 'Горный', 'Степь', 'Поморье',
              'Тайга', 'Луг', 'Причал', 'Мельница', 'Табун', 'Кедр', 'Ягода', 'Хмель',
              'Рыбак', 'Соль', 'Камень', 'Ремесло', 'Двор', 'Улей', 'Борозда', 'Покос']

COMMUNITY = [('Соседи', 'Соседское'), ('Мастера', 'Профессиональное'),
             ('Пчеловоды', 'Профессиональное'), ('Сыроделы', 'Профессиональное'),
             ('Родители', 'Соседское'), ('Велосипедисты', 'По интересам'),
             ('Садоводы', 'По интересам'), ('Столяры', 'Профессиональное'),
             ('Фермеры', 'Профессиональное'), ('Ткачи', 'Профессиональное'),
             ('Пекари', 'Профессиональное'), ('Кузнецы', 'Профессиональное'),
             ('Волонтёры', 'По интересам'), ('Айтишники', 'Профессиональное'),
             ('Овцеводы', 'Профессиональное'), ('Рыбаки', 'По интересам'),
             ('Пасечники', 'Профессиональное'), ('Дачники', 'Соседское')]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, s):
    io.open(os.path.join(ROOT, p), 'w', encoding='utf-8', newline='').write(s)


def fio():
    if random.random() < 0.45:
        return '%sа %s %s' % (random.choice(SURNAMES_M), random.choice(NAMES_F), random.choice(PATR_F))
    return '%s %s %s' % (random.choice(SURNAMES_M), random.choice(NAMES_M), random.choice(PATR_M))


def slug(text, i):
    base = re.sub(r'[^a-zа-яё0-9]+', '-', text.lower()).strip('-')
    return '%s-%d' % (base[:40], i)


def set_attr(card, attr, value):
    return re.sub(r'(%s=")[^"]*(")' % attr, lambda m: m.group(1) + value + m.group(2), card, count=1)


def swap_city(card, old_city, new_city):
    """Город меняется и в атрибуте фильтра, и во всех видимых местах карточки."""
    card = set_attr(card, 'data-city', new_city)
    return card.replace(old_city, new_city)


def cards_of(s, pattern):
    return [m.group(0) for m in re.finditer(pattern, s, re.S)]


def fill(path, pattern, mutate, counter=None):
    s = read(path)
    found = list(re.finditer(pattern, s, re.S))
    have = len(found)
    if have >= TARGET:
        print('%-24s уже %d — не трогаю' % (path, have))
        return
    need = TARGET - have
    samples = [m.group(0) for m in found]
    tail = found[-1].end()
    chunk = ''.join('\n' + mutate(random.choice(samples), i) for i in range(need))
    s = s[:tail] + chunk + s[tail:]
    if counter:
        s = re.sub(counter[0], counter[1], s, count=1)
    write(path, s)
    print('%-24s было %3d, добавлено %3d, стало %3d' % (path, have, need, have + need))


# ─────────────────────────── правила по каталогам ───────────────────────────

def m_people(card, i):
    name = fio()
    city = random.choice(CITIES)
    old = re.search(r'data-city="([^"]*)"', card).group(1)
    card = swap_city(card, old, city)
    card = set_attr(card, 'data-trust', str(random.randint(55, 99)))
    card = set_attr(card, 'data-fav-id', slug(name, i))
    card = re.sub(r'(<div class="vacancy-title">)[^<]*', lambda m: m.group(1) + name, card, count=1)
    card = re.sub(r'(alt=")[^"]*(")', lambda m: m.group(1) + name + m.group(2), card, count=1)
    card = re.sub(r'images/avatars/\d+\.jpg', 'images/avatars/%d.jpg' % random.choice(
        [4, 5, 6, 8, 9, 10, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
         31, 32, 33, 34, 35, 36, 37, 38, 39, 44, 45, 47, 48, 51, 52, 53]), card)
    card = re.sub(r'(\d+) (лет|года)', lambda m: '%d %s' % (random.randint(21, 64), m.group(2)), card, count=1)
    card = re.sub(r'Уровень доверия \d+%', 'Уровень доверия %d%%' % random.randint(55, 99), card, count=1)
    return card


def m_titleonly(titles, title_class='vacancy-title'):
    def mutate(card, i):
        title = random.choice(titles)
        city = random.choice(CITIES)
        m = re.search(r'data-city="([^"]*)"', card)
        if m:
            card = swap_city(card, m.group(1), city)
        card = set_attr(card, 'data-fav-id', slug(title, i))
        card = re.sub(r'(<div class="%s">)[^<]*' % title_class,
                      lambda mm: mm.group(1) + title, card, count=1)
        return card
    return mutate


def m_org(card, i):
    kind = random.choice(['Кооператив «%s»', 'СПК «%s»', 'ООО «%s»', 'ПК «%s»',
                          'Фонд «%s»', 'АО «%s»', 'ТСЖ «%s»'])
    name = kind % random.choice(COOP_WORDS)
    city = random.choice(CITIES)
    m = re.search(r'data-city="([^"]*)"', card)
    if m:
        card = swap_city(card, m.group(1), city)
    card = set_attr(card, 'data-trust', str(random.randint(58, 99)))
    card = set_attr(card, 'data-fav-id', slug(name, i))
    card = re.sub(r'(<div class="pname">)[^<]*', lambda mm: mm.group(1) + name, card, count=1)
    card = re.sub(r'(alt=")[^"]*(")', lambda mm: mm.group(1) + name + mm.group(2), card, count=1)
    return card


def m_project(card, i):
    name = random.choice([
        'Круглогодичная теплица', 'Сыроварня кооператива', 'Солнечная станция посёлка',
        'Пекарня полного цикла', 'Цех переработки шерсти', 'Овощехранилище',
        'Мастерская по ремонту техники', 'Пасека на 120 ульев', 'Модульный дом из бруса',
        'Молочный цех', 'Питомник саженцев', 'Кузнечная мастерская', 'Коворкинг в райцентре',
        'Пункт приёма вторсырья', 'Сушильный комплекс', 'Рыбное хозяйство',
        'Гончарная мастерская', 'Мельница на паях', 'Ткацкая артель', 'Медпункт на селе',
        'Общественная баня', 'Тепличный комбинат', 'Сельский музей', 'Ремонт моста',
        'Детская площадка', 'Библиотека инструментов', 'Зарядная станция', 'Ветряк на 25 кВт'])
    city = random.choice(CITIES)
    m = re.search(r'data-city="([^"]*)"', card)
    if m:
        card = swap_city(card, m.group(1), city)
    r = random.randint(5, 99)
    card = set_attr(card, 'data-readiness', str(r))
    card = set_attr(card, 'data-fav-id', slug(name, i))
    card = re.sub(r'(<div class="pname">)[^<]*', lambda mm: mm.group(1) + name, card, count=1)
    card = re.sub(r'(<div class="readiness-pct">)\d+%', lambda mm: mm.group(1) + '%d%%' % r, card, count=1)
    card = re.sub(r'(alt=")[^"]*(")', lambda mm: mm.group(1) + name + mm.group(2), card, count=1)
    return card


def m_resource(card, i):
    name = random.choice([
        'Мини-трактор МТЗ', 'Сеялка точного высева', 'Пресс-подборщик', 'Молоковоз',
        'Сушилка для зерна', 'Инкубатор на 500 яиц', 'Доильный аппарат', 'Мотоблок',
        'Бетономешалка 180 л', 'Сварочный аппарат', 'Леса строительные', 'Опалубка',
        'Пиломатериал обрезной', 'Цемент М500', 'Утеплитель минеральный', 'Профлист',
        'Мёд разнотравье', 'Сыр полутвёрдый', 'Молоко фермерское', 'Картофель семенной',
        'Шерсть овечья мытая', 'Саженцы яблони', 'Комбикорм', 'Сено в рулонах',
        'Помещение под цех', 'Холодильная камера', 'Прицеп самосвальный', 'Генератор 5 кВт',
        'Мобильная пилорама', 'Гончарный круг', 'Ткацкий станок', 'Пекарская печь'])
    city = random.choice(CITIES)
    m = re.search(r'data-city="([^"]*)"', card)
    if m:
        card = swap_city(card, m.group(1), city)
    price = random.choice([120, 250, 380, 450, 620, 900, 1400, 2600, 4800, 9500, 18000, 42000])
    card = set_attr(card, 'data-price', str(price))
    card = set_attr(card, 'data-fav-id', slug(name, i))
    card = re.sub(r'(<div class="pname">)[^<]*', lambda mm: mm.group(1) + name, card, count=1)
    card = re.sub(r'от [\d\s]+ ₽', 'от %s ₽' % '{:,}'.format(price).replace(',', ' '), card, count=1)
    card = re.sub(r'(alt=")[^"]*(")', lambda mm: mm.group(1) + name + mm.group(2), card, count=1)
    return card


def m_community(card, i):
    base, kind = random.choice(COMMUNITY)
    city = random.choice(CITIES)
    name = '%s — %s' % (base, city)
    m = re.search(r'data-city="([^"]*)"', card)
    if m:
        card = swap_city(card, m.group(1), city)
    card = set_attr(card, 'data-type', kind)
    card = set_attr(card, 'data-group', slug(name, i))
    card = set_attr(card, 'data-fav-id', slug(name, i))
    card = re.sub(r'(<div class="vacancy-title">)[^<]*', lambda mm: mm.group(1) + name, card, count=1)
    card = re.sub(r'\d+ участник\w*', '%d участников' % random.randint(12, 840), card, count=1)
    return card


def m_deal(card, i):
    subject = random.choice([
        'Пиломатериал, 8 м³', 'Мёд разнотравье, 40 кг', 'Аренда трактора, 5 суток',
        'Сыр полутвёрдый, 60 кг', 'Ремонт кровли цеха', 'Шерсть мытая, 200 кг',
        'Комбикорм, 3 тонны', 'Электромонтаж теплицы', 'Саженцы яблони, 300 шт',
        'Перевозка молока, месяц', 'Доля 3% в проекте «Пекарня»', 'Картофель семенной, 1,2 т',
        'Аренда холодильной камеры', 'Сварочные работы', 'Сено в рулонах, 90 шт',
        'Установка солнечных панелей', 'Обучение сыроделию', 'Разработка сайта кооператива'])
    org = random.choice(['Кооператив «%s»', 'СПК «%s»', 'ООО «%s»', 'ПК «%s»']) % random.choice(COOP_WORDS)
    city = random.choice(CITIES)
    m = re.search(r'data-city="([^"]*)"', card)
    if m:
        card = swap_city(card, m.group(1), city)
    amount = random.choice([8600, 12400, 18600, 24000, 41400, 63000, 92000, 128000, 240000])
    card = re.sub(r'(<a class="deal-title"[^>]*>)[^<]*', lambda mm: mm.group(1) + subject, card, count=1)
    card = re.sub(r'(<div class="review-name">)[^<]*', lambda mm: mm.group(1) + org, card, count=1)
    card = re.sub(r'(<div class="deal-amount">)[^<]*', lambda mm: mm.group(1) +
                  '{:,}'.format(amount).replace(',', ' ') + ' ₽', card, count=1)
    card = re.sub(r'(<span class="deal-doc-no"[^>]*>)[^<]*',
                  lambda mm: mm.group(1) + 'СД-2026-%06d' % (140 + i), card, count=1)
    card = set_attr(card, 'data-search', (subject + ' ' + org).lower() + ' сд-2026-%06d' % (140 + i))
    return card


SKILLS = ['Электромонтаж', 'Кирпичная кладка', 'Сварка полуавтоматом', 'Столярное дело',
          'Кровельные работы', 'Штукатурные работы', 'Плиточные работы', 'Сантехника',
          'Ремонт двигателей', 'Управление трактором', 'Доение и уход за скотом',
          'Пчеловодство', 'Сыроделие', 'Хлебопечение', 'Ткачество', 'Гончарное дело',
          'Кузнечное дело', 'Обработка шерсти', 'Ветеринария', 'Агрономия',
          'Бухгалтерия кооператива', 'Юридическое сопровождение', 'Веб-разработка',
          'Дизайн упаковки', 'Фотосъёмка продукции', 'Логистика и развоз',
          'Работа на пилораме', 'Монтаж теплиц', 'Установка солнечных панелей',
          'Ремонт бытовой техники', 'Пошив изделий', 'Резьба по дереву']

VACANCIES = ['Электромонтажник', 'Кладовщик', 'Прораб', 'Тракторист', 'Доярка',
             'Пекарь', 'Сыродел', 'Сварщик', 'Водитель категории C', 'Агроном',
             'Ветеринарный фельдшер', 'Бухгалтер кооператива', 'Менеджер по закупкам',
             'Оператор доильного зала', 'Пасечник', 'Столяр', 'Швея', 'Гончар',
             'Кузнец', 'Логист', 'Мастер по ремонту техники', 'Продавец в лавке',
             'Разнорабочий', 'Технолог пищевого производства', 'Скотник', 'Пильщик']


def main():
    fill('people.html', r'<a class="vacancy-card".*?</a>\n', m_people,
         (r'<span id="people-count">\d+</span>', '<span id="people-count">100</span>'))
    fill('skills.html', r'<a class="vacancy-card".*?</a>\n', m_titleonly(SKILLS))
    fill('vacancies.html', r'<a class="vacancy-card".*?</a>\n', m_titleonly(VACANCIES))
    fill('communities.html', r'<div class="vacancy-card".*?\n      </div>\n', m_community)
    fill('projects.html', r'<a class="ptile".*?</a>\n', m_project)
    fill('organizations.html', r'<a class="ptile".*?</a>\n', m_org)
    fill('resources.html', r'<a class="ptile".*?</a>\n', m_resource)
    fill('deals.html', r'<article class="deal-card".*?</article>\n', m_deal)


if __name__ == '__main__':
    sys.exit(main())
