# -*- coding: utf-8 -*-
"""Журнал событий узла: конверт, подпись, хэш-цепочка.

Каждый узел сети ведёт свой журнал — только дописываемый и связанный
хэшами. Событие ссылается на предыдущее поле `prev`, поэтому вырезать или
подменить запись в середине нельзя, не переписав весь хвост, а хвост подписан.

Порядок внутри журнала — полный: за него отвечает `seq`. Порядка между
журналами разных узлов нет и не нужно: у каждого факта ровно один
авторитетный узел — тот, о ком факт. Двусторонние объекты (сделка)
продвигаются, только когда в обоих журналах есть подписанные события.

Здесь — эталон формата, а не рабочий узел: ни сети, ни хранилища.
"""
import base64
import re

from . import canonical, ed25519

VERSION = 1
UNSIGNED = ('id', 'sig')                 # поля, которых нет под подписью
TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
DID_RE = re.compile(r'^did:web:[a-z0-9.\-]+(:[A-Za-z0-9.\-_%]+)*$')


class Invalid(Exception):
    """Событие или цепочка не проходят проверку."""


def b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode('ascii')


def unb64(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def payload(event):
    """То, что подписывается: событие без id и подписи."""
    return {k: v for k, v in event.items() if k not in UNSIGNED}


def make(node, kid, seq, prev, ts, type_, subject, body, to=None, attachments=None):
    """Собрать конверт. Порядок ключей не важен — сериализация каноническая."""
    event = {
        'v': VERSION,
        'node': node,
        'kid': kid,
        'seq': seq,
        'prev': prev,
        'ts': ts,
        'type': type_,
        'subject': subject,
        'body': body,
    }
    if to is not None:
        event['to'] = list(to)
    if attachments:
        event['attachments'] = list(attachments)
    return event


def sign(event, secret):
    """Подписать конверт: добавляет id и sig, исходный словарь не трогает."""
    signed = dict(event)
    for field in UNSIGNED:
        signed.pop(field, None)
    raw = canonical.encode(signed)
    signed['id'] = canonical.digest(payload(signed))
    signed['sig'] = b64(ed25519.sign(secret, raw))
    return signed


def check(event, public_key):
    """Проверить одно событие. Бросает Invalid с внятной причиной."""
    if event.get('v') != VERSION:
        raise Invalid('версия конверта %r, поддерживается %d' % (event.get('v'), VERSION))
    for field in ('node', 'kid', 'seq', 'ts', 'type', 'subject', 'body', 'id', 'sig'):
        if field not in event:
            raise Invalid('нет обязательного поля %s' % field)
    if not DID_RE.match(event['node']):
        raise Invalid('идентификатор узла не похож на did:web: %r' % event['node'])
    if not event['kid'].startswith(event['node'] + '#'):
        raise Invalid('ключ %r принадлежит не этому узлу' % event['kid'])
    if not isinstance(event['seq'], int) or event['seq'] < 0:
        raise Invalid('seq должен быть целым неотрицательным')
    if not TS_RE.match(event['ts']):
        raise Invalid('время не в формате 2026-09-01T10:00:00Z: %r' % event['ts'])
    if (event['seq'] == 0) != (event.get('prev') is None):
        raise Invalid('первое событие журнала и только оно имеет prev = null')

    body = payload(event)
    if canonical.digest(body) != event['id']:
        raise Invalid('id не совпадает с хэшем содержимого — событие изменено')
    if not ed25519.verify(public_key, canonical.encode(body), unb64(event['sig'])):
        raise Invalid('подпись не проходит проверку')
    return True


def check_chain(events, public_key):
    """Проверить непрерывность и подлинность журнала целиком."""
    previous = None
    for index, event in enumerate(events):
        check(event, public_key)
        if previous is None:
            if event['seq'] != 0:
                raise Invalid('журнал начинается с seq %d, а не с нуля' % event['seq'])
        else:
            if event['seq'] != previous['seq'] + 1:
                raise Invalid('разрыв в нумерации на позиции %d: %d после %d'
                              % (index, event['seq'], previous['seq']))
            if event['prev'] != previous['id']:
                raise Invalid('разрыв цепочки на позиции %d: prev не тот' % index)
            if event['node'] != previous['node']:
                raise Invalid('в одном журнале события разных узлов')
        previous = event
    return True


class Log(object):
    """Журнал одного узла в памяти — для тестов и примеров."""

    def __init__(self, node, kid, secret):
        self.node = node
        self.kid = kid
        self.secret = secret
        self.public_key = ed25519.public_key(secret)
        self.events = []

    def append(self, ts, type_, subject, body, to=None, attachments=None):
        last = self.events[-1] if self.events else None
        event = make(
            node=self.node, kid=self.kid,
            seq=0 if last is None else last['seq'] + 1,
            prev=None if last is None else last['id'],
            ts=ts, type_=type_, subject=subject, body=body,
            to=to, attachments=attachments,
        )
        signed = sign(event, self.secret)
        self.events.append(signed)
        return signed

    def since(self, seq=0, limit=100):
        """Выдача для GET /federation/log — узел догоняет журнал порциями."""
        return [e for e in self.events if e['seq'] >= seq][:limit]

    def verify(self):
        return check_chain(self.events, self.public_key)
