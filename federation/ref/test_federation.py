# -*- coding: utf-8 -*-
"""Тесты справочной реализации.

Запуск:  python federation/ref/test_federation.py
Ничего, кроме стандартной библиотеки, не требуется.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from federation.ref import canonical, deal, ed25519, log   # noqa: E402


class Ed25519Vectors(unittest.TestCase):
    """Векторы RFC 8032 §7.1 — иначе нельзя утверждать, что подпись правильная."""

    VECTORS = [
        ('9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60',
         'd75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a',
         '',
         'e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a3'
         '3bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b'),
        ('4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb',
         '3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c',
         '72',
         '92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15'
         '996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00'),
        ('c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7',
         'fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025',
         'af82',
         '6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16'
         'f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a'),
    ]

    def test_public_key(self):
        for secret, public, _, _ in self.VECTORS:
            self.assertEqual(ed25519.public_key(bytes.fromhex(secret)).hex(), public)

    def test_sign(self):
        for secret, _, message, signature in self.VECTORS:
            got = ed25519.sign(bytes.fromhex(secret), bytes.fromhex(message))
            self.assertEqual(got.hex(), signature)

    def test_verify(self):
        for _, public, message, signature in self.VECTORS:
            self.assertTrue(ed25519.verify(
                bytes.fromhex(public), bytes.fromhex(message), bytes.fromhex(signature)))

    def test_reject_tampered(self):
        secret, public, message, _ = self.VECTORS[1]
        signature = bytearray(ed25519.sign(bytes.fromhex(secret), bytes.fromhex(message)))
        signature[0] ^= 1
        self.assertFalse(ed25519.verify(
            bytes.fromhex(public), bytes.fromhex(message), bytes(signature)))

    def test_reject_malleable(self):
        """Подпись со скаляром больше порядка группы принимать нельзя."""
        _, public, message, signature = self.VECTORS[1]
        raw = bytearray(bytes.fromhex(signature))
        raw[63] |= 0xF0
        self.assertFalse(ed25519.verify(
            bytes.fromhex(public), bytes.fromhex(message), bytes(raw)))


class Canonical(unittest.TestCase):

    def test_key_order_does_not_matter(self):
        first = {'b': 1, 'a': 2, 'ё': 3}
        second = {'ё': 3, 'a': 2, 'b': 1}
        self.assertEqual(canonical.encode(first), canonical.encode(second))
        self.assertEqual(canonical.digest(first), canonical.digest(second))

    def test_no_whitespace(self):
        self.assertEqual(canonical.dumps({'a': [1, 2], 'b': {'c': None}}),
                         '{"a":[1,2],"b":{"c":null}}')

    def test_escapes(self):
        self.assertEqual(canonical.dumps('строка\n\t"кавычка"\\'),
                         '"строка\\n\\t\\"кавычка\\"\\\\"')
        self.assertEqual(canonical.dumps('\x00\x1f'), '"\\u0000\\u001f"')

    def test_floats_rejected(self):
        """Дробное число — источник расхождения подписей между языками."""
        with self.assertRaises(TypeError):
            canonical.dumps({'сумма': 1234.56})

    def test_money_as_string(self):
        self.assertEqual(canonical.dumps({'сумма': '1234.56', 'валюта': 'RUB'}),
                         '{"валюта":"RUB","сумма":"1234.56"}')

    def test_unicode_kept_as_is(self):
        self.assertEqual(canonical.encode('пай'), '"пай"'.encode('utf-8'))


NODE_A = 'did:web:coop-borozda.example.ru'
NODE_B = 'did:web:artel-severnyy-les.example.ru'
SECRET_A = bytes(range(32))
SECRET_B = bytes(range(32, 64))
DEAL = NODE_A + '/deal/СД-2026-000101'


def _log(node, secret):
    return log.Log(node, node + '#key-1', secret)


class Envelope(unittest.TestCase):

    def setUp(self):
        self.log = _log(NODE_A, SECRET_A)

    def test_sign_and_check(self):
        event = self.log.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL,
                                {'сумма': '150000.00', 'валюта': 'RUB'})
        self.assertTrue(log.check(event, self.log.public_key))

    def test_id_is_digest_of_content(self):
        event = self.log.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.assertEqual(event['id'], canonical.digest(log.payload(event)))

    def test_tampered_body_rejected(self):
        event = self.log.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL,
                                {'сумма': '150000.00'})
        event['body']['сумма'] = '15000.00'
        with self.assertRaises(log.Invalid):
            log.check(event, self.log.public_key)

    def test_foreign_key_rejected(self):
        event = self.log.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        other = ed25519.public_key(SECRET_B)
        with self.assertRaises(log.Invalid):
            log.check(event, other)

    def test_key_must_belong_to_node(self):
        event = self.log.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        event['kid'] = NODE_B + '#key-1'
        with self.assertRaises(log.Invalid):
            log.check(event, self.log.public_key)

    def test_timestamp_format(self):
        event = self.log.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        event['ts'] = '01.09.2026 10:00'
        with self.assertRaises(log.Invalid):
            log.check(event, self.log.public_key)


class Chain(unittest.TestCase):

    def setUp(self):
        self.log = _log(NODE_A, SECRET_A)
        for index in range(5):
            self.log.append('2026-09-01T10:0%d:00Z' % index, 'catalog.offer.published',
                            NODE_A + '/offer/%d' % index, {'название': 'Мука в/с'})

    def test_chain_verifies(self):
        self.assertTrue(self.log.verify())

    def test_first_event_has_no_prev(self):
        self.assertIsNone(self.log.events[0]['prev'])
        self.assertEqual(self.log.events[0]['seq'], 0)

    def test_removed_event_breaks_chain(self):
        broken = self.log.events[:2] + self.log.events[3:]
        with self.assertRaises(log.Invalid):
            log.check_chain(broken, self.log.public_key)

    def test_reordered_events_break_chain(self):
        broken = list(self.log.events)
        broken[2], broken[3] = broken[3], broken[2]
        with self.assertRaises(log.Invalid):
            log.check_chain(broken, self.log.public_key)

    def test_since_paginates(self):
        self.assertEqual([e['seq'] for e in self.log.since(2, limit=2)], [2, 3])

    def test_catching_up_after_offline(self):
        """Узел был офлайн, догоняет с той позиции, на которой остановился."""
        seen = self.log.since(0, limit=2)
        rest = self.log.since(seen[-1]['seq'] + 1, limit=100)
        self.assertTrue(log.check_chain(seen + rest, self.log.public_key))
        self.assertEqual(len(seen) + len(rest), 5)


class BilateralDeal(unittest.TestCase):
    """Состояние сделки — функция двух журналов, а не запись в одном."""

    def setUp(self):
        self.a = _log(NODE_A, SECRET_A)
        self.b = _log(NODE_B, SECRET_B)
        self.parties = (NODE_A, NODE_B)

    def merged(self):
        return self.a.events + self.b.events

    def test_nothing_before_proposal(self):
        self.assertIsNone(deal.state(DEAL, self.parties, self.merged()))

    def test_proposed_then_accepted(self):
        self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {'сумма': '150000.00'})
        self.assertEqual(deal.state(DEAL, self.parties, self.merged()), deal.PROPOSED)
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.assertEqual(deal.state(DEAL, self.parties, self.merged()), deal.ACCEPTED)

    def test_one_signature_is_not_enough(self):
        self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {})
        self.assertEqual(deal.state(DEAL, self.parties, self.merged()), deal.AWAITING)
        self.assertEqual(deal.missing_signature(DEAL, self.parties, self.merged()), NODE_B)

    def test_both_signatures_close_the_deal(self):
        self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {})
        self.b.append('2026-09-02T10:00:00Z', 'deal.act.signed', DEAL, {})
        self.assertEqual(deal.state(DEAL, self.parties, self.merged()), deal.DONE)
        self.assertIsNone(deal.missing_signature(DEAL, self.parties, self.merged()))

    def test_order_of_arrival_does_not_matter(self):
        """События приходят с задержкой и вперемешку — состояние то же."""
        self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {})
        self.b.append('2026-09-02T10:00:00Z', 'deal.act.signed', DEAL, {})
        shuffled = list(reversed(self.merged()))
        self.assertEqual(deal.state(DEAL, self.parties, shuffled), deal.DONE)

    def test_third_party_cannot_close_a_deal(self):
        """Чужой узел подписывает что угодно — на состояние это не влияет."""
        outsider = _log('did:web:chuzhoy.example.ru', bytes(range(64, 96)))
        self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {})
        outsider.append('2026-09-02T09:30:00Z', 'deal.act.signed', DEAL, {})
        events = self.merged() + outsider.events
        self.assertEqual(deal.state(DEAL, self.parties, events), deal.AWAITING)

    def test_dispute_wins_over_everything(self):
        self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {})
        self.b.append('2026-09-02T10:00:00Z', 'deal.act.signed', DEAL, {})
        self.b.append('2026-09-03T10:00:00Z', 'deal.disputed', DEAL, {'причина': 'недовоз'})
        self.assertEqual(deal.state(DEAL, self.parties, self.merged()), deal.DISPUTED)

    def test_counterparty_cannot_forge_my_signature(self):
        """Подделать событие от чужого имени нельзя: подпись не сойдётся."""
        forged = dict(self.a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {}))
        forged['node'] = NODE_B
        with self.assertRaises(log.Invalid):
            log.check(forged, ed25519.public_key(SECRET_B))


if __name__ == '__main__':
    unittest.main(verbosity=2)
