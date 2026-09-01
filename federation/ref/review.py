# -*- coding: utf-8 -*-
"""Двусторонний отзыв с одновременным раскрытием.

Обычные отзывы на площадках устроены так, что второй пишет, увидев первого.
Отсюда две беды: месть за плохую оценку и подстройка своей оценки под чужую.
Люди перестают писать правду, и рейтинг превращается в вежливость.

Здесь два шага. Сначала каждая сторона публикует **хэш** своего отзыва —
обязательство, из которого нельзя узнать оценку, но которое нельзя потом
переписать. Когда обязательства есть у обеих сторон, отзывы раскрываются
одновременно.

Свойство, ради которого всё затевалось: увидев чужую оценку, свою поменять
уже нельзя — она зафиксирована хэшем. Проверяется тестом
`test_cannot_change_review_after_seeing_the_other`.

Соль обязательна. Без неё оценок всего пять, и хэш подбирается перебором за
доли секунды — обязательство перестаёт что-либо скрывать.
"""
from . import canonical

VERSION = 1

CLOSED = 'closed'        # ждём, пока обе стороны возьмут обязательство
AWAITING = 'awaiting'    # обязательства есть, раскрылась одна сторона
OPEN = 'open'            # раскрыты обе — показываем


class Invalid(Exception):
    """Отзыв не проходит проверку."""


def _body(deal, author, rating, text, salt):
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        raise Invalid('оценка — целое от одного до пяти')
    if not salt or len(salt) < 16:
        raise Invalid('соль обязательна и не короче шестнадцати знаков: '
                      'без неё оценка подбирается перебором')
    return {'v': VERSION, 'deal': deal, 'author': author,
            'rating': rating, 'text': text, 'salt': salt}


def commit(deal, author, rating, text, salt):
    """Обязательство: хэш отзыва без самого отзыва."""
    return {'v': VERSION, 'deal': deal, 'author': author,
            'hash': canonical.digest(_body(deal, author, rating, text, salt))}


def reveal(deal, author, rating, text, salt):
    """Раскрытие: тот же отзыв целиком."""
    return _body(deal, author, rating, text, salt)


def matches(commitment, revealed):
    """Раскрытое должно соответствовать взятому обязательству."""
    if commitment['deal'] != revealed['deal'] or commitment['author'] != revealed['author']:
        raise Invalid('раскрытие относится к другому отзыву')
    return canonical.digest(revealed) == commitment['hash']


def disclosure(deal, parties, commitments, revelations, after_deadline=False):
    """Состояние раскрытия по сделке.

    До истечения срока отзывы показываются, только когда раскрылись обе
    стороны. После срока показывается то, что раскрыто: молчание одной
    стороны не должно держать чужой отзыв закрытым вечно.
    """
    if len(parties) != 2:
        raise Invalid('у сделки ровно две стороны')
    committed = {c['author'] for c in commitments
                 if c['deal'] == deal and c['author'] in parties}
    revealed = {r['author'] for r in revelations
                if r['deal'] == deal and r['author'] in parties}
    if after_deadline and revealed:
        return OPEN
    if len(committed) < 2:
        return CLOSED
    if len(revealed) < 2:
        return AWAITING
    return OPEN


def visible(deal, parties, commitments, revelations, after_deadline=False):
    """Отзывы, которые можно показать. Раскрытие без обязательства не в счёт.

    Проверка обязательна: иначе сторона могла бы «раскрыть» не то, что
    обещала, увидев чужую оценку.
    """
    if disclosure(deal, parties, commitments, revelations, after_deadline) != OPEN:
        return []
    by_author = {}
    for one in commitments:
        if one['deal'] == deal and one['author'] in parties:
            by_author[one['author']] = one
    out = []
    for revealed in revelations:
        if revealed['deal'] != deal or revealed['author'] not in parties:
            continue
        commitment = by_author.get(revealed['author'])
        if commitment is None:
            raise Invalid('раскрытие без обязательства: %s' % revealed['author'])
        if not matches(commitment, revealed):
            raise Invalid('раскрытие не соответствует обязательству: %s' % revealed['author'])
        out.append(revealed)
    return out
