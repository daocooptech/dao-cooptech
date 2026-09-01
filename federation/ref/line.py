# -*- coding: utf-8 -*-
"""Линия взаимного обязательства и раунд взаимозачёта.

## Почему линия — исключение из правила владения

У каждого факта в сети ровно один авторитетный узел — тот, о ком факт. У
двустороннего обязательства такого узла нет: оно симметрично по природе.
«Ты мне должен» без встречной подписи — не факт, а заявление.

Поэтому линия A—B устроена как цепочка состояний: у каждого свой номер
версии, ссылка на хэш предыдущего состояния и **две подписи**. Ни одна
сторона не может переписать линию в одиночку, а две разные записи с одним
номером версии — доказуемое нарушение: у пострадавшего на руках две подписи
контрагента под одним номером.

Для бухгалтера это не «распределённый реестр», а акт сверки, подписываемый
после каждой операции. Так и называть в интерфейсе.

## Почему зачёт по кругу — раунд, а не автомат

Односторонний зачёт (ст. 410 ГК) работает только между двумя лицами со
встречными требованиями. В круге A→B→C→A встречности нет ни в одной паре,
поэтому круговой зачёт — многосторонняя сделка всех участников.

Отсюда устройство: координатор видит граф долгов и предлагает раунд, но
списать ничего не может. Раунд применяется только при полном комплекте
подписей и отменяется целиком при неполном — частичный зачёт делает одних
должников лучше, других хуже. Комплект подписей самодостаточен: если
координатор упал после сбора, раунд применит любой участник, потому что
операция идемпотентна по хэшу таблицы.

Как только координатор получает право держать остатки, он становится
банком, и власть сети концентрируется у оператора платформы. Этого здесь
нет и быть не должно.
"""
from decimal import Decimal

from . import canonical, ed25519, log

VERSION = 1
CURRENCY_RE = log.re.compile(r'^[A-Z]{3}$')


class Invalid(log.Invalid):
    """Линия или раунд не проходят проверку."""


def line_id(one, other):
    """Идентификатор линии не зависит от того, кто её открыл."""
    if one == other:
        raise Invalid('линия с самим собой не бывает')
    return '|'.join(sorted([one, other]))


def parties(line):
    return tuple(line.split('|'))


def money(amount, currency='RUB'):
    return {'amount': amount, 'currency': currency}


def _amount(value):
    """Суммы всегда строкой: дробные числа дают разные байты в разных языках."""
    if not isinstance(value.get('amount'), str):
        raise Invalid('сумма передаётся строкой, а не числом')
    if not CURRENCY_RE.match(value.get('currency', '')):
        raise Invalid('валюта — три заглавные буквы по ISO 4217')
    return Decimal(value['amount'])


def state(line, version, prev, balance, basis, ts):
    """Состояние линии.

    `balance` — знаковая сумма с точки зрения первой стороны линии
    (лексикографически меньшего идентификатора): положительная означает, что
    вторая сторона должна первой. Знак вместо двух полей выбран потому, что
    сальдо по ходу работы перетекает из стороны в сторону, и «должник» —
    это свойство момента, а не участника.
    """
    if version < 1:
        raise Invalid('версии линии начинаются с единицы')
    if (version == 1) != (prev is None):
        raise Invalid('первое состояние линии и только оно не ссылается на предыдущее')
    _amount(balance)
    return {
        'v': VERSION,
        'line': line,
        'version': version,
        'prev': prev,
        'balance': balance,
        'basis': basis,
        'ts': ts,
    }


def state_id(st):
    """Хэш состояния без подписей — то, что подписывают обе стороны."""
    return canonical.digest({k: v for k, v in st.items() if k != 'sigs'})


def sign(st, who, secret):
    """Подписать состояние. Возвращает копию: исходник не меняется."""
    if who not in parties(st['line']):
        raise Invalid('подписать линию может только её сторона')
    signed = dict(st)
    signed['sigs'] = dict(st.get('sigs') or {})
    body = canonical.encode({k: v for k, v in st.items() if k != 'sigs'})
    signed['sigs'][who] = log.b64(ed25519.sign(secret, body))
    return signed


def check_state(st, keys):
    """Состояние действительно только с подписями обеих сторон.

    `keys` — идентификатор стороны в открытый ключ.
    """
    if st.get('v') != VERSION:
        raise Invalid('версия формата линии %r' % st.get('v'))
    both = parties(st['line'])
    sigs = st.get('sigs') or {}
    unknown = set(sigs) - set(both)
    if unknown:
        raise Invalid('подпись постороннего: %s' % ', '.join(sorted(unknown)))
    body = canonical.encode({k: v for k, v in st.items() if k != 'sigs'})
    for who in both:
        if who not in sigs:
            raise Invalid('нет подписи стороны %s' % who)
        if who not in keys:
            raise Invalid('неизвестен ключ стороны %s' % who)
        if not ed25519.verify(keys[who], body, log.unb64(sigs[who])):
            raise Invalid('подпись стороны %s не проходит проверку' % who)
    return True


def check_line(states, keys):
    """Проверить цепочку состояний линии целиком."""
    previous = None
    for index, st in enumerate(states):
        check_state(st, keys)
        if previous is None:
            if st['version'] != 1:
                raise Invalid('линия начинается с версии %d' % st['version'])
        else:
            if st['line'] != previous['line']:
                raise Invalid('в одной цепочке состояния разных линий')
            if st['version'] != previous['version'] + 1:
                raise Invalid('разрыв в версиях на позиции %d' % index)
            if st['prev'] != state_id(previous):
                raise Invalid('разрыв цепочки линии на позиции %d' % index)
        previous = st
    return True


def find_fork(states):
    """Две разные записи с одним номером версии — доказуемое нарушение.

    Возвращает пару состояний или None. Предотвратить форк нельзя: узел
    физически способен подписать два разных состояния. Зато его можно
    обнаружить, и у пострадавшего останутся обе подписи контрагента под
    одним номером — этого достаточно для разбирательства.
    """
    seen = {}
    for st in states:
        key = (st['line'], st['version'])
        digest = state_id(st)
        if key in seen and seen[key][0] != digest:
            return (seen[key][1], st)
        seen.setdefault(key, (digest, st))
    return None


def balance_of(st, who):
    """Сальдо с точки зрения указанной стороны: минус — вы должны."""
    first, second = parties(st['line'])
    value = _amount(st['balance'])
    if who == first:
        return value
    if who == second:
        return -value
    raise Invalid('%s не сторона этой линии' % who)


# ── Раунд взаимозачёта ──────────────────────────────────────────────────

def round_(coordinator, participants, entries, deadline, currency='RUB'):
    """Предложение раунда: кто кому насколько уменьшает обязательство.

    Координатор — тот, кто нашёл круг и предложил таблицу. Прав на списание
    у него нет: каждое звено подписывает уменьшение своего обязательства само.
    """
    if len(set(participants)) < 2:
        raise Invalid('в раунде меньше двух участников')
    for entry in entries:
        _amount(entry['amount'])
        if entry['debtor'] == entry['creditor']:
            raise Invalid('звено само себе не должно')
        for side in ('debtor', 'creditor'):
            if entry[side] not in participants:
                raise Invalid('%s не в списке участников раунда' % entry[side])
        if entry['amount']['currency'] != currency:
            raise Invalid('в одном раунде одна валюта: требования должны быть однородны')
    return {
        'v': VERSION,
        'coordinator': coordinator,
        'participants': sorted(set(participants)),
        'entries': entries,
        'currency': currency,
        'deadline': deadline,
    }


def round_id(rnd):
    """Хэш таблицы зачёта. По нему раунд идемпотентен: применение дважды
    даёт тот же результат, поэтому падение координатора после сбора подписей
    ничего не ломает."""
    return canonical.digest(rnd)


def net_effect(rnd):
    """На сколько меняется чистая позиция каждого участника."""
    effect = {who: Decimal('0') for who in rnd['participants']}
    for entry in rnd['entries']:
        value = _amount(entry['amount'])
        effect[entry['debtor']] += value      # долг уменьшился — позиция вверх
        effect[entry['creditor']] -= value    # требование уменьшилось — вниз
    return effect


def check_round(rnd):
    """Раунд обязан быть нейтральным: он гасит встречные долги, а не
    перекладывает их с одного участника на другого.

    Проверка не формальность. Несбалансированная таблица — это скрытый
    перевод долга, на который участник соглашается, думая, что подписывает
    взаимозачёт.
    """
    effect = net_effect(rnd)
    if sum(effect.values()) != 0:
        raise Invalid('таблица зачёта не сходится: сумма изменений не ноль')
    for who, value in effect.items():
        if value < 0:
            raise Invalid('зачёт ухудшает позицию участника %s' % who)
    return True


def sign_round(rnd, who, secret):
    """Подпись под конкретной таблицей: подменить её после сбора нельзя."""
    if who not in rnd['participants']:
        raise Invalid('подписать раунд может только его участник')
    return {'round': round_id(rnd), 'by': who,
            'sig': log.b64(ed25519.sign(secret, round_id(rnd).encode('ascii')))}


def collected(rnd, signatures, keys):
    """Кого ещё ждём. Пустой список означает полный комплект."""
    valid = set()
    for item in signatures:
        if item['round'] != round_id(rnd):
            continue                                  # подпись под другой таблицей
        who = item['by']
        if who not in rnd['participants'] or who not in keys:
            continue
        if ed25519.verify(keys[who], round_id(rnd).encode('ascii'), log.unb64(item['sig'])):
            valid.add(who)
    return [who for who in rnd['participants'] if who not in valid]


def apply_round(rnd, signatures, keys, balances):
    """Применить раунд к сальдо линий.

    Только при полном комплекте подписей. Неполный комплект — не повод
    применить частично: раунд отменяется целиком и пересобирается на
    суженном множестве участников.
    """
    check_round(rnd)
    missing = collected(rnd, signatures, keys)
    if missing:
        raise Invalid('нет подписей: %s' % ', '.join(missing))
    result = dict(balances)
    for entry in rnd['entries']:
        line = line_id(entry['debtor'], entry['creditor'])
        first, _second = parties(line)
        value = _amount(entry['amount'])
        # Сальдо хранится со знаком от первой стороны линии.
        delta = -value if entry['creditor'] == first else value
        result[line] = str(Decimal(result.get(line, '0')) + delta)
    return result
