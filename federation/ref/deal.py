# -*- coding: utf-8 -*-
"""Состояние сделки выводится из двух журналов, а не хранится в одном.

Главная мысль всей схемы. У сделки две равные стороны, и ни одна не вправе
объявить состояние за обоих. Поэтому состояние нигде не записано — оно
вычисляется из подписанных событий обеих сторон:

    предложена      -> есть deal.proposed от инициатора
    отклонена       -> есть deal.rejected от второй стороны
    принята         -> есть deal.accepted от второй стороны
    ждёт вторую     -> акт подписан одной стороной
    исполнена       -> акт подписан обеими
    спор            -> любая из сторон заявила deal.disputed

Отсюда следует, что общий консенсус сети не нужен: договариваются двое, и
достаточно двух подписей. Ни блокчейн, ни распределённая база с разрешением
конфликтов для этого не требуются.

События третьих узлов игнорируются: сторона сделки — только `parties`.
"""

PROPOSED = 'proposed'
ACCEPTED = 'accepted'
REJECTED = 'rejected'
AWAITING = 'awaiting_counterparty'
DONE = 'done'
DISPUTED = 'disputed'

# Для интерфейса: то, что видит кооператор, без слова «узел».
RUSSIAN = {
    PROPOSED: 'Предложена',
    ACCEPTED: 'Принята',
    REJECTED: 'Отклонена',
    AWAITING: 'Ожидает подписи второй стороны',
    DONE: 'Исполнена',
    DISPUTED: 'Спор',
}


def state(deal_subject, parties, events):
    """Состояние сделки по событиям обеих сторон.

    deal_subject — идентификатор сделки, parties — два идентификатора узлов
    (did:web), events — события из обоих журналов в любом порядке.
    """
    if len(parties) != 2:
        raise ValueError('у сделки ровно две стороны')

    mine = [e for e in events
            if e.get('subject') == deal_subject and e.get('node') in parties]

    def by(type_):
        return {e['node'] for e in mine if e.get('type') == type_}

    if by('deal.disputed'):
        return DISPUTED
    if by('deal.rejected'):
        return REJECTED

    signed_act = by('deal.act.signed')
    if len(signed_act) == 2:
        return DONE
    if len(signed_act) == 1:
        return AWAITING
    if by('deal.accepted'):
        return ACCEPTED
    if by('deal.proposed'):
        return PROPOSED
    return None


def missing_signature(deal_subject, parties, events):
    """Кого именно ждём. Нужно интерфейсу: «ждём подписи кооператива N»."""
    if state(deal_subject, parties, events) != AWAITING:
        return None
    signed = {e['node'] for e in events
              if e.get('subject') == deal_subject and e.get('type') == 'deal.act.signed'}
    return next(node for node in parties if node not in signed)
