# -*- coding: utf-8 -*-
"""Наполнить биржу складских мощностей (ext-warehouse.html) до правила «100–200».

На бирже было тринадцать объявлений — на них не видно ни фильтров по виду
хранения и сроку, ни листателя, ни того, как экран держится под нагрузкой.

Владельцы берутся из готовых наборов data/people.js и data/organizations.js:
объявление ведёт на карточку человека или организации, которые на платформе
действительно есть. Выдуманных имён здесь нет.

Написанные руками объявления не трогаются: скрипт владеет только тем, что
между маркерами, и при повторном запуске файл не меняется.

Запуск:  python tools/gen-warehouse.py            — записать
         python tools/gen-warehouse.py --check    — показать, что получится
"""
import io, os, re, sys, json, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CHECK = "--check" in sys.argv

BEGIN = "    /* ── ниже собрано tools/gen-warehouse.py, руками не правим ── */"
END = "    /* ── конец собранного ── */"

# вид хранения: фотографии, единица, что бывает в характеристиках
KINDS = {
    "heated": (["warehouse.jpg", "warehouse-shelves.jpg", "craft-workshop.jpg",
                "carpentry-shop.jpg", "sewing-workshop.jpg", "makerspace.jpg",
                "flour-mill.jpg", "bakery.jpg"],
               ["м²", "паллетомест"],
               ["Высота <b>6 м</b>", "Высота <b>8 м</b>", "Две рампы", "Одна рампа",
                "Стеллажи", "Учёт партий", "Пожарная сигнализация", "Круглосуточный доступ",
                "Погрузчик на месте", "Видеонаблюдение"]),
    "dry": (["grain-silo.jpg", "cattle-barn.jpg", "garage-building.jpg", "hay-bales.jpg",
             "sawmill-logs.jpg", "timber-beam.jpg", "wood-planks.jpg"],
            ["м²", "тонн", "м³"],
            ["Бетонный пол", "Ворота 4 м", "Сухая вентиляция", "Отдельный въезд",
             "Охрана по периметру", "Навес над разгрузкой", "Весовая на въезде"]),
    "chill": (["cold-storage.jpg", "milk-tank.jpg", "meat-shop.jpg", "cheese-making.jpg",
               "potato-crate.jpg", "berry-harvest.jpg"],
              ["паллетомест", "м²", "тонн"],
              ["Термограф", "Две камеры", "Приёмка по температуре", "Мойка тары",
               "Отгрузка по заявке за сутки", "Санитарный паспорт"]),
    "freeze": (["chest-freezer.jpg", "cold-storage.jpg", "beef-meat.jpg", "pork-meat.jpg",
                "pelmeni.jpg", "meat-band-saw.jpg"],
               ["паллетомест", "тонн"],
               ["Термограф", "Резервное питание", "Шоковая заморозка",
                "Отгрузка по заявке за сутки", "Раздельные камеры"]),
    "open": (["land-plot.jpg", "brick-stack.jpg", "scaffolding.jpg", "rebar-steel.jpg",
              "cement-bag.jpg", "waste-sorting.jpg", "cargo-truck.jpg"],
             ["м²", "тонн"],
             ["Твёрдое покрытие", "Въезд для фур", "Освещение", "Охрана",
              "Кран-балка", "Отсыпка щебнем", "Ограждение"]),
}
KIND_NAMES = {
    "heated": "сухого отапливаемого хранения",
    "dry": "сухого неотапливаемого хранения",
    "chill": "холодильного хранения",
    "freeze": "морозильного хранения",
    "open": "открытой площадки",
}
OFFER_TITLES = {
    "heated": ["Сухой отапливаемый склад класса B", "Отапливаемый склад с рампой",
               "Тёплый склад под фасовку", "Отапливаемое помещение под мастерскую",
               "Склад класса C с отоплением"],
    "dry": ["Неотапливаемый склад под стройматериалы", "Ангар под сезонное хранение",
            "Сухой склад под зерно", "Крытая площадка под пиломатериалы",
            "Гараж-склад под инвентарь"],
    "chill": ["Холодильная камера +2…+6 °C", "Холодильник под овощи и корнеплоды",
              "Камера охлаждения под молочное", "Холодильное хранение ягоды"],
    "freeze": ["Морозильная камера −18 °C", "Низкотемпературное хранение мяса",
               "Морозильник под полуфабрикаты", "Камера шоковой заморозки"],
    "open": ["Открытая площадка под стройматериалы", "Площадка под технику и контейнеры",
             "Открытое хранение сыпучих", "Площадка с твёрдым покрытием"],
}
DEMAND_GOODS = {
    "heated": ["цемент", "сухие смеси", "готовую продукцию", "фасованный товар", "утеплитель"],
    "dry": ["пиломатериалы", "зерно", "сено", "инвентарь", "кирпич"],
    "chill": ["овощи", "молочное", "ягоду", "саженцы", "сыр"],
    "freeze": ["полуфабрикаты", "мясо", "рыбу", "ягоду", "пельмени"],
    "open": ["стройматериалы", "технику", "контейнеры", "щебень", "трубы"],
}
PERIODS = ["short", "long", "forever"]
PERIOD_WORD = {"short": "до 3 месяцев", "long": "от 3 месяцев", "forever": "бессрочно"}

# Единица измерения тянет за собой всё: и как называется цена («за тонну»,
# а не «за тонн»), и за какой срок её считают, и сколько такого влезает
# в помещение. Первый прогон генератора этого не знал и выдал склад
# на 2400 тонн с ценой за паллетоместо.
UNITS = {
    "м²":          {"price": "м²",          "per": "в месяц", "rate": (70, 620),
                    "total": (120, 2400), "block": (200, 600)},
    "тонн":        {"price": "тонну",       "per": "в месяц", "rate": (300, 1900),
                    "total": (40, 900),   "block": (20, 120)},
    "паллетомест": {"price": "паллетоместо", "per": "в сутки", "rate": (18, 240),
                    "total": (40, 600),   "block": (20, 100)},
    "м³":          {"price": "м³",          "per": "в месяц", "rate": (150, 900),
                    "total": (100, 3000), "block": (50, 300)},
}

TERM_NOTES = {
    "rent": ["от одной недели", "от 3 месяцев, депозит один месяц", "помесячно, без депозита",
             "от 6 месяцев", "с правом досрочного расторжения"],
    "custody": ["с приёмкой, учётом и отгрузкой", "учёт по партиям, отчёт раз в неделю",
                "приёмка по температуре", "с погрузчиком и оператором"],
    "project": ["для проектов на платформе, вместо оплаты", "вместо оплаты — участие в марже",
                "доля в результате, а не в имуществе"],
    "buyout": ["с выделением доли в общей площадке", "с оформлением через кооператив",
               "рассрочка до года"],
    "share": ["паевой взнос вместо аренды", "с правом пользования по графику",
              "возврат пая при выходе"],
    "barter": ["встречное хранение в другом городе", "обмен мощностями по сезону"],
}


def load(path, var):
    s = io.open(path, encoding="utf-8").read()
    return json.loads(s[s.index("["):s.rindex("]") + 1])


def js(v):
    """Строка в кавычках так, как её пишут руками в этом файле."""
    return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"


def entry(e, ind="    "):
    lines = []
    head = ("side: %s, id: %s, city: %s, kind: %s, party: %s, period: %s"
            % (js(e["side"]), js(e["id"]), js(e["city"]), js(e["kind"]),
               js(e["party"]), js(e["period"])))
    lines.append(ind + "{")
    lines.append(ind + "  " + head + ",")
    lines.append(ind + "  title: %s," % js(e["title"]))
    lines.append(ind + "  photo: %s," % js(e["photo"]))
    o = e["owner"]
    lines.append(ind + "  owner: { name: %s, avatar: %s, link: %s, trust: %d%s },"
                 % (js(o["name"]), js(o["avatar"]), js(o["link"]), o["trust"],
                    ", logo: true" if o.get("logo") else ""))
    if e["side"] == "offer":
        lines.append(ind + "  unit: %s, total: %d, free: %d,"
                     % (js(e["unit"]), e["total"], e["free"]))
    else:
        lines.append(ind + "  unit: %s, need: %d," % (js(e["unit"]), e["need"]))
    lines.append(ind + "  specs: [%s]," % ", ".join(js(s) for s in e["specs"]))
    lines.append(ind + "  terms: [")
    for t in e["terms"]:
        lines.append(ind + "    { key: %s, value: %s, note: %s },"
                     % (js(t["key"]), js(t["value"]), js(t["note"])))
    lines[-1] = lines[-1][:-1]
    lines.append(ind + "  ]")
    lines.append(ind + "},")
    return "\n".join(lines) + "\n"


def money(n):
    return "{:,}".format(n).replace(",", " ")


def build(count=112):
    rnd = random.Random(20260909)
    people = load("data/people.js", "PEOPLE")
    orgs = load("data/organizations.js", "ORGANIZATIONS")
    out, used_ids = [], set()

    for i in range(count):
        kind = rnd.choice(list(KINDS))
        photos, units, specs_pool = KINDS[kind]
        side = "offer" if rnd.random() < 0.68 else "demand"
        as_org = rnd.random() < 0.55
        if as_org:
            src = rnd.choice([o for o in orgs if o.get("img") and o.get("trust")])
            owner = {"name": src["title"], "avatar": src["img"],
                     "link": "organization.html?id=" + src["id"],
                     "trust": int(src["trust"]), "logo": True}
            party = "Организация"
        else:
            src = rnd.choice([p for p in people if p.get("avatar") and p.get("trust")])
            owner = {"name": src["name"], "avatar": src["avatar"],
                     "link": "person.html?id=" + src["id"],
                     "trust": int(src["trust"])}
            party = "Человек"
        city = src["city"] if src["city"] != "Удалённо" else "Тюмень"
        unit = rnd.choice(units)

        lo, hi = UNITS[unit]["total"]
        if side == "offer":
            title = rnd.choice(OFFER_TITLES[kind])
            total = rnd.randrange(lo, hi, 10)
            free = int(total * rnd.uniform(0.15, 0.75) / 10) * 10 or 10
            need = 0
        else:
            need = rnd.randrange(max(20, lo // 3), max(40, hi // 2), 10)
            title = "Нужно %d %s %s под %s" % (
                need, unit, KIND_NAMES[kind], rnd.choice(DEMAND_GOODS[kind]))
            total = free = 0

        eid = re.sub(r"[^a-z0-9]+", "-", (owner["link"].split("=")[-1] + "-" + kind))[:40]
        eid = "wh-%s-%d" % (eid.strip("-"), i + 1)
        if eid in used_ids:
            continue
        used_ids.add(eid)

        u = UNITS[unit]
        keys = rnd.sample(["rent", "custody", "project", "buyout", "share", "barter"],
                          rnd.randint(2, 3))
        terms = []
        for k in keys:
            if k == "rent":
                value = "%s ₽/%s %s" % (money(rnd.randrange(*u["rate"], 10)),
                                        u["price"], u["per"])
            elif k == "custody":
                lo, hi = u["rate"]
                value = "%s ₽/%s %s" % (money(rnd.randrange(int(lo * 1.2), int(hi * 1.3), 10)),
                                        u["price"], u["per"])
            elif k == "project":
                value = "доля %d%%" % rnd.randint(3, 12)
            elif k == "buyout":
                block = rnd.randrange(*u["block"], 10)
                value = "%s ₽ за блок %s %s" % (
                    money(rnd.randrange(900000, 6400000, 50000)), money(block), unit)
            elif k == "share":
                value = "пай от %s ₽" % money(rnd.randrange(120000, 1400000, 10000))
            else:
                value = "обмен на %s %s" % (money(rnd.randrange(*u["block"], 10)), unit)
            terms.append({"key": k, "value": value, "note": rnd.choice(TERM_NOTES[k])})

        out.append({
            "side": side, "id": eid, "city": city, "kind": kind, "party": party,
            "period": rnd.choice(PERIODS),
            "title": title,
            "photo": "images/photos/" + rnd.choice(photos),
            "owner": owner, "unit": unit, "total": total, "free": free, "need": need,
            "specs": rnd.sample(specs_pool, rnd.randint(2, 4)),
            "terms": terms,
        })
    return out


def main():
    s = io.open("ext-warehouse.html", encoding="utf-8").read()
    items = build()
    block = BEGIN + "\n" + "".join(entry(e) for e in items) + END + "\n"

    if BEGIN in s:
        s = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n",
                   lambda m: block, s, flags=re.S)
    else:
        anchor = "  var MARKET = [\n"
        assert anchor in s, "не найден MARKET"
        s = s.replace(anchor, anchor + block, 1)

    hand = len(re.findall(r"side: '(?:offer|demand)', id: '(?!wh-)", s))
    # число на вкладке «Биржа мощностей» было проставлено руками — держим в согласии
    s = re.sub(r'(data-tab="market">Биржа мощностей <span class="badge outline">)\d+(</span>)',
               lambda m: m.group(1) + str(len(items) + hand) + m.group(2), s)
    print("своих объявлений:", len(items), "· руками:", hand, "· всего:", len(items) + hand)
    print("предложений:", sum(1 for e in items if e["side"] == "offer"),
          "· запросов:", sum(1 for e in items if e["side"] == "demand"))
    print("длиннейший заголовок:", max(len(e["title"]) for e in items))
    if CHECK:
        print("(пробный запуск, файл не тронут)")
        return
    io.open("ext-warehouse.html", "w", encoding="utf-8", newline="\n").write(s)
    print("записано в ext-warehouse.html")


main()
