# -*- coding: utf-8 -*-
"""Правила, найденные при подготовке переноса на движок 28.09.2026.

Каждый класс закрывает одну дыру первой версии эталона:

1. `for` в GET /federation/log верили на слово — теперь читатель подписывает запрос;
2. инициатор мог сам принять свою оферту;
3. два акта без оферты и акцепта «исполняли» сделку; событие о чужом предмете
   проходило проверку;
4. did:web с портом не проходил проверку;
5. не было ни построителя, ни разбора DID-документа;
6. в DID-документе не было отметки компрометации;
7. из спора не было выхода.

Запуск:  python federation/ref/run_tests.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from federation.ref import deal, did, ed25519, log, ownership, reader   # noqa: E402

NOW = '2026-09-28T12:00:00Z'
NODE_A = 'did:web:koop-borozda.example.ru'
NODE_B = 'did:web:artel-severnyy-les.example.ru'
NODE_C = 'did:web:storonniy.example.ru'
SECRET_A = bytes(range(32))
SECRET_B = bytes(range(32, 64))
SECRET_C = bytes(range(64, 96))
DEAL = NODE_A + '/deal/0b5c6f5e-3d2a-4c8e-9a51-7f3b2e1d9c40'


def _log(node, secret):
    return log.Log(node, node + '#key-1', secret)


class _DealBase(unittest.TestCase):
    """Общие помощники; своих тестов нет."""

    def setUp(self):
        self.a = _log(NODE_A, SECRET_A)
        self.b = _log(NODE_B, SECRET_B)
        self.parties = (NODE_A, NODE_B)
        self.offer = self.a.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL,
                                   {'total': {'amount': '150000.00', 'currency': 'RUB'}},
                                   to=[NODE_B])

    def events(self, *extra):
        return self.a.events + self.b.events + list(extra)

    def reply(self, journal, ts, type_, refs=None, **body):
        body['refs'] = self.offer['id'] if refs is None else refs
        return journal.append(ts, type_, DEAL, body)

    def state(self, *extra):
        return deal.state(DEAL, self.parties, self.events(*extra))

    def accept(self):
        return self.reply(self.b, '2026-09-01T11:00:00Z', 'deal.accepted')


class DealRoles(_DealBase):
    """Дыры 2 и 3: кто вправе предлагать, принимать и подписывать акт."""

    def test_initiator_is_who_minted_the_subject(self):
        self.assertEqual(deal.initiator(DEAL, self.parties), NODE_A)
        self.assertEqual(deal.initiator(DEAL, (NODE_B, NODE_A)), NODE_A)
        self.assertIsNone(deal.initiator(NODE_C + '/deal/1', self.parties))

    def test_initiator_cannot_accept_own_offer(self):
        self.reply(self.a, '2026-09-01T10:05:00Z', 'deal.accepted')
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_initiator_cannot_reject_own_offer(self):
        self.reply(self.a, '2026-09-01T10:05:00Z', 'deal.rejected', reason='передумал')
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_counterparty_cannot_propose_on_foreign_subject(self):
        """Предмет выпускает инициатор: оферта B о предмете A не засчитывается."""
        a = _log(NODE_A, SECRET_A)
        b = _log(NODE_B, SECRET_B)
        b.append('2026-09-01T10:00:00Z', 'deal.proposed', DEAL, {})
        self.assertIsNone(deal.state(DEAL, self.parties, a.events + b.events))

    def test_acceptance_without_refs_does_not_count(self):
        self.b.append('2026-09-01T11:00:00Z', 'deal.accepted', DEAL, {})
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_acceptance_of_another_offer_does_not_count(self):
        self.reply(self.b, '2026-09-01T11:00:00Z', 'deal.accepted', refs='0' * 64)
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_redacted_acceptance_is_not_evidence(self):
        """Без тела не видно, на что ссылается ответ, — не засчитываем."""
        accepted = log.redact(self.accept())
        events = self.a.events + [accepted]
        self.assertEqual(deal.state(DEAL, self.parties, events), deal.PROPOSED)

    def test_two_acts_without_offer_do_not_close_a_deal(self):
        a = _log(NODE_A, SECRET_A)
        b = _log(NODE_B, SECRET_B)
        a.append('2026-09-02T09:00:00Z', 'deal.act.signed', DEAL, {'refs': '1' * 64})
        b.append('2026-09-02T10:00:00Z', 'deal.act.signed', DEAL, {'refs': '1' * 64})
        self.assertIsNone(deal.state(DEAL, self.parties, a.events + b.events))

    def test_acts_before_acceptance_do_not_close_a_deal(self):
        self.reply(self.a, '2026-09-02T09:00:00Z', 'deal.act.signed')
        self.reply(self.b, '2026-09-02T10:00:00Z', 'deal.act.signed')
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_withdrawn_before_acceptance(self):
        self.reply(self.a, '2026-09-01T10:30:00Z', 'deal.withdrawn')
        self.assertEqual(self.state(), deal.WITHDRAWN)

    def test_counterparty_cannot_withdraw_foreign_offer(self):
        self.reply(self.b, '2026-09-01T10:30:00Z', 'deal.withdrawn')
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_rejected(self):
        self.reply(self.b, '2026-09-01T11:00:00Z', 'deal.rejected', reason='дорого')
        self.assertEqual(self.state(), deal.REJECTED)

    def test_withdraw_and_accept_race_is_a_dispute(self):
        """Порядка между журналами нет: кто раньше — не рассудить."""
        self.reply(self.a, '2026-09-01T10:59:00Z', 'deal.withdrawn')
        self.accept()
        self.assertEqual(self.state(), deal.DISPUTED)

    def test_accept_and_reject_together_is_a_dispute(self):
        self.accept()
        self.reply(self.b, '2026-09-01T11:01:00Z', 'deal.rejected', reason='ошибся')
        self.assertEqual(self.state(), deal.DISPUTED)

    def test_started_after_acceptance(self):
        self.accept()
        self.reply(self.a, '2026-09-01T12:00:00Z', 'deal.started')
        self.assertEqual(self.state(), deal.ACTIVE)

    def test_started_before_acceptance_does_not_count(self):
        self.reply(self.a, '2026-09-01T10:10:00Z', 'deal.started')
        self.assertEqual(self.state(), deal.PROPOSED)

    def test_every_state_has_a_russian_name(self):
        for value in (deal.PROPOSED, deal.WITHDRAWN, deal.ACCEPTED, deal.REJECTED, deal.ACTIVE,
                      deal.AWAITING, deal.DONE, deal.DISPUTED, deal.CANCELLED):
            self.assertIn(value, deal.RUSSIAN)


class DisputeSettlement(_DealBase):
    """Дыра 7: из спора выходят только вместе."""

    def setUp(self):
        _DealBase.setUp(self)
        self.accept()
        self.dispute = self.reply(self.b, '2026-09-03T10:00:00Z', 'deal.disputed',
                                  reason='недовоз')

    def settle(self, journal, ts, outcome, settles=None):
        return self.reply(journal, ts, 'deal.dispute.settled', outcome=outcome,
                          settles=[self.dispute['id']] if settles is None else settles)

    def test_one_side_cannot_settle(self):
        self.settle(self.a, '2026-09-04T10:00:00Z', 'done')
        self.assertEqual(self.state(), deal.DISPUTED)

    def test_both_sides_settle_as_done(self):
        self.settle(self.a, '2026-09-04T10:00:00Z', 'done')
        self.settle(self.b, '2026-09-04T11:00:00Z', 'done')
        self.assertEqual(self.state(), deal.DONE)

    def test_both_sides_settle_as_cancelled(self):
        self.settle(self.a, '2026-09-04T10:00:00Z', 'cancelled')
        self.settle(self.b, '2026-09-04T11:00:00Z', 'cancelled')
        self.assertEqual(self.state(), deal.CANCELLED)

    def test_different_outcomes_stay_disputed(self):
        self.settle(self.a, '2026-09-04T10:00:00Z', 'done')
        self.settle(self.b, '2026-09-04T11:00:00Z', 'cancelled')
        self.assertEqual(self.state(), deal.DISPUTED)

    def test_new_dispute_reopens(self):
        """Урегулирование закрывает только перечисленные заявления о споре."""
        self.settle(self.a, '2026-09-04T10:00:00Z', 'done')
        self.settle(self.b, '2026-09-04T11:00:00Z', 'done')
        self.reply(self.a, '2026-09-05T10:00:00Z', 'deal.disputed', reason='брак')
        self.assertEqual(self.state(), deal.DISPUTED)

    def test_third_party_cannot_settle(self):
        outsider = _log(NODE_C, SECRET_C)
        self.settle(self.a, '2026-09-04T10:00:00Z', 'done')
        self.settle(outsider, '2026-09-04T11:00:00Z', 'done')
        self.assertEqual(self.state(*outsider.events), deal.DISPUTED)

    def test_unknown_outcome_ignored(self):
        self.settle(self.a, '2026-09-04T10:00:00Z', 'как-нибудь')
        self.settle(self.b, '2026-09-04T11:00:00Z', 'как-нибудь')
        self.assertEqual(self.state(), deal.DISPUTED)


class Payments(_DealBase):
    """Оплату подтверждает получатель; суммы складываются десятично."""

    def pay(self, journal, ts, amount, currency='RUB'):
        return self.reply(journal, ts, 'deal.payment.received',
                          amount={'amount': amount, 'currency': currency})

    def test_nothing_paid_before_acceptance(self):
        self.pay(self.a, '2026-09-01T10:30:00Z', '100.00')
        self.assertEqual(deal.paid(DEAL, self.parties, self.events()), {})

    def test_sums_by_currency_without_float(self):
        self.accept()
        self.pay(self.a, '2026-09-02T10:00:00Z', '0.10')
        self.pay(self.a, '2026-09-02T11:00:00Z', '0.20')
        self.pay(self.a, '2026-09-02T12:00:00Z', '10.00', 'CNY')
        self.assertEqual(deal.paid(DEAL, self.parties, self.events()),
                         {'RUB': '0.30', 'CNY': '10.00'})

    def test_duplicate_delivery_counted_once(self):
        self.accept()
        payment = self.pay(self.a, '2026-09-02T10:00:00Z', '500.00')
        self.assertEqual(deal.paid(DEAL, self.parties, self.events(payment)), {'RUB': '500.00'})

    def test_third_party_payment_ignored(self):
        self.accept()
        outsider = _log(NODE_C, SECRET_C)
        self.pay(outsider, '2026-09-02T10:00:00Z', '999.00')
        self.assertEqual(deal.paid(DEAL, self.parties, self.events(*outsider.events)), {})


class Ownership(unittest.TestCase):
    """Дыра 3: подпись доказывает автора, но не его право на предмет."""

    def event(self, type_, node, subject):
        return {'type': type_, 'node': node, 'subject': subject}

    def test_own_offer(self):
        self.assertIs(ownership.owns(self.event('catalog.offer.withdrawn', NODE_A,
                                                NODE_A + '/offer/17')), True)

    def test_foreign_offer_rejected(self):
        self.assertIs(ownership.owns(self.event('catalog.offer.withdrawn', NODE_A,
                                                NODE_B + '/offer/17')), False)

    def test_lookalike_domain_rejected(self):
        """did:web:a.ru не владеет did:web:a.ru.evil — сравнение по «/», а не по началу строки."""
        self.assertIs(ownership.owns(self.event('catalog.offer.published', NODE_A,
                                                NODE_A + '.evil.ru/offer/1')), False)

    def test_node_events_are_about_the_node_itself(self):
        self.assertIs(ownership.owns(self.event('node.announced', NODE_A, NODE_A)), True)
        self.assertIs(ownership.owns(self.event('node.key.rotated', NODE_A, NODE_B)), False)

    def test_bilateral_needs_context(self):
        for type_ in ('deal.accepted', 'line.state.signed', 'clearing.round.signed',
                      'review.revealed', 'membership.admitted', 'joint.signed'):
            self.assertEqual(ownership.owns(self.event(type_, NODE_B, DEAL)),
                             ownership.NEEDS_CONTEXT)

    def test_unknown_type_is_not_judged(self):
        self.assertEqual(ownership.owns(self.event('weather.reported', NODE_A, NODE_B + '/x')),
                         ownership.UNKNOWN)

    def test_deal_author(self):
        parties = (NODE_A, NODE_B)
        self.assertTrue(ownership.deal_author_ok(self.event('deal.proposed', NODE_A, DEAL), parties))
        self.assertFalse(ownership.deal_author_ok(self.event('deal.proposed', NODE_B, DEAL), parties))
        self.assertTrue(ownership.deal_author_ok(self.event('deal.accepted', NODE_B, DEAL), parties))
        self.assertFalse(ownership.deal_author_ok(self.event('deal.accepted', NODE_C, DEAL), parties))


class DidWithPort(unittest.TestCase):
    """Дыра 4: второй узел на стенде живёт на порту."""

    def test_port_accepted(self):
        for value in ('did:web:localhost%3A8070', 'did:web:fed-b.koopeh.test%3A8070',
                      'did:web:hub.example.ru:org:borozda'):
            self.assertTrue(log.DID_RE.match(value), value)

    def test_garbage_rejected(self):
        for value in ('did:web:Localhost', 'did:web:host%3Aabc', 'did:key:z6Mk', 'did:web:'):
            self.assertFalse(log.DID_RE.match(value), value)

    def test_event_from_node_with_port_verifies(self):
        node = 'did:web:localhost%3A8070'
        journal = _log(node, SECRET_B)
        event = journal.append('2026-09-28T11:00:00Z', 'node.announced', node, {'name': 'Узел Б'})
        self.assertEqual(log.check(event, journal.keyring(), NOW), log.OK)


class DidDocument(unittest.TestCase):
    """Дыры 5 и 6: документ с ключами и отметка компрометации."""

    def test_base58_vectors(self):
        # draft-msporny-base58, раздел 5
        self.assertEqual(did.b58encode(b'Hello World!'), '2NEpo7TZRRrLZSi2U')
        self.assertEqual(did.b58encode(bytes.fromhex('0000287fb4cd')), '11233QC4')
        self.assertEqual(did.b58decode('11233QC4'), bytes.fromhex('0000287fb4cd'))
        self.assertEqual(did.b58encode(b''), '')

    def test_multibase_prefix_and_roundtrip(self):
        public = ed25519.public_key(SECRET_A)
        text = did.multibase(public)
        self.assertTrue(text.startswith('z6Mk'))
        self.assertEqual(did.from_multibase(text), public)

    def test_multibase_rejects_other_keys(self):
        with self.assertRaises(log.Invalid):
            did.from_multibase('z' + did.b58encode(b'\xe7\x01' + bytes(33)))   # secp256k1
        with self.assertRaises(log.Invalid):
            did.from_multibase('f' + '00' * 34)

    def test_url_by_spec(self):
        self.assertEqual(did.url('did:web:w3c-ccg.github.io'),
                         'https://w3c-ccg.github.io/.well-known/did.json')
        self.assertEqual(did.url('did:web:w3c-ccg.github.io:user:alice'),
                         'https://w3c-ccg.github.io/user/alice/did.json')
        self.assertEqual(did.url('did:web:example.com%3A3000'),
                         'https://example.com:3000/.well-known/did.json')
        self.assertEqual(did.url('did:web:localhost%3A8070', scheme='http'),
                         'http://localhost:8070/.well-known/did.json')

    def test_document_roundtrip_verifies_events(self):
        journal = _log(NODE_A, SECRET_A)
        event = journal.append('2026-09-01T10:00:00Z', 'node.announced', NODE_A, {'name': 'Борозда'})
        doc = did.document(NODE_A, [{'kid': journal.kid, 'public_key': journal.public_key}])
        self.assertEqual(doc['verificationMethod'][0]['type'], 'Ed25519VerificationKey2020')
        ring = did.keyring(doc, NODE_A)
        self.assertEqual(log.check(event, ring, NOW), log.OK)

    def test_document_for_another_node_rejected(self):
        doc = did.document(NODE_B, [{'kid': NODE_B + '#key-1',
                                     'public_key': ed25519.public_key(SECRET_B)}])
        with self.assertRaises(log.Invalid):
            did.keyring(doc, NODE_A)

    def test_foreign_key_in_document_rejected(self):
        doc = did.document(NODE_A, [{'kid': NODE_A + '#key-1',
                                     'public_key': ed25519.public_key(SECRET_A)}])
        doc['verificationMethod'][0]['id'] = NODE_B + '#key-1'
        with self.assertRaises(log.Invalid):
            did.keyring(doc, NODE_A)
        with self.assertRaises(log.Invalid):
            did.document(NODE_A, [{'kid': NODE_B + '#key-1',
                                   'public_key': ed25519.public_key(SECRET_B)}])

    def test_unknown_key_type_skipped(self):
        doc = did.document(NODE_A, [{'kid': NODE_A + '#key-1',
                                     'public_key': ed25519.public_key(SECRET_A)}])
        doc['verificationMethod'].append({'id': NODE_A + '#key-9', 'type': 'JsonWebKey2020'})
        self.assertEqual(list(did.keyring(doc, NODE_A).keys), [NODE_A + '#key-1'])

    def test_compromise_marks_later_events_suspect(self):
        journal = _log(NODE_A, SECRET_A)
        before = journal.append('2026-09-01T10:00:00Z', 'node.announced', NODE_A, {})
        after = journal.append('2026-09-20T10:00:00Z', 'catalog.offer.published',
                               NODE_A + '/offer/1', {})
        doc = did.document(NODE_A, [{'kid': journal.kid, 'public_key': journal.public_key,
                                     'compromised': '2026-09-15T00:00:00Z'}])
        self.assertEqual(doc['verificationMethod'][0]['compromised'], '2026-09-15T00:00:00Z')
        ring = did.keyring(doc, NODE_A)
        self.assertEqual(log.check(before, ring, NOW), log.OK)
        self.assertEqual(log.check(after, ring, NOW), log.SUSPECT)

    def test_planned_revocation_differs_from_compromise(self):
        journal = _log(NODE_A, SECRET_A)
        before = journal.append('2026-09-01T10:00:00Z', 'node.announced', NODE_A, {})
        after = journal.append('2026-09-20T10:00:00Z', 'catalog.offer.published',
                               NODE_A + '/offer/1', {})
        doc = did.document(NODE_A, [{'kid': journal.kid, 'public_key': journal.public_key,
                                     'revoked': '2026-09-15T00:00:00Z'}])
        ring = did.keyring(doc, NODE_A)
        self.assertEqual(log.check(before, ring, NOW), log.OK)
        with self.assertRaises(log.Invalid):
            log.check(after, ring, NOW)


class ReaderProof(unittest.TestCase):
    """Дыра 1: тело адресного события получает только доказавший, что он адресат."""

    PATH = '/federation/log'

    def setUp(self):
        self.a = _log(NODE_A, SECRET_A)
        self.a.append('2026-09-28T10:00:00Z', 'node.announced', NODE_A, {'name': 'Борозда'})
        self.a.append('2026-09-28T10:01:00Z', 'deal.proposed', DEAL,
                      {'total': {'amount': '150000.00', 'currency': 'RUB'}}, to=[NODE_B])
        # Ключи тех, кто может прийти читать: как если бы их DID-документы уже скачаны.
        self.readers = (log.KeyRing()
                        .add(NODE_B + '#key-1', ed25519.public_key(SECRET_B))
                        .add(NODE_C + '#key-1', ed25519.public_key(SECRET_C)))

    def fetch(self, query, headers=None):
        return reader.serve(self.a, headers or {}, self.PATH, query, self.readers, NOW)

    def signed(self, who, secret, query, ts='2026-09-28T11:59:00Z', claim=None):
        return reader.sign(claim or who, who + '#key-1', secret, 'GET', self.PATH, query, ts)

    def test_signed_addressee_gets_the_body(self):
        query = {'since': '0', 'for': NODE_B}
        events = self.fetch(query, self.signed(NODE_B, SECRET_B, query))
        self.assertIn('body', events[1])

    def test_claim_without_signature_gets_redacted(self):
        events = self.fetch({'since': '0', 'for': NODE_B})
        self.assertNotIn('body', events[1])
        self.assertIn('body', events[0])                # широковещательное видно всем

    def test_outsider_pretending_to_be_addressee_gets_redacted(self):
        query = {'since': '0', 'for': NODE_B}
        headers = reader.sign(NODE_B, NODE_C + '#key-1', SECRET_C, 'GET', self.PATH, query,
                              '2026-09-28T11:59:00Z')
        self.assertNotIn('body', self.fetch(query, headers)[1])

    def test_signature_with_wrong_secret_gets_redacted(self):
        query = {'since': '0', 'for': NODE_B}
        headers = reader.sign(NODE_B, NODE_B + '#key-1', SECRET_C, 'GET', self.PATH, query,
                              '2026-09-28T11:59:00Z')
        self.assertNotIn('body', self.fetch(query, headers)[1])

    def test_for_must_match_signer(self):
        query = {'since': '0', 'for': NODE_B}
        headers = self.signed(NODE_C, SECRET_C, {'since': '0', 'for': NODE_C})
        self.assertNotIn('body', self.fetch(query, headers)[1])

    def test_stale_request_gets_redacted(self):
        query = {'since': '0', 'for': NODE_B}
        headers = self.signed(NODE_B, SECRET_B, query, ts='2026-09-28T11:50:00Z')
        self.assertNotIn('body', self.fetch(query, headers)[1])

    def test_altered_query_gets_redacted(self):
        headers = self.signed(NODE_B, SECRET_B, {'since': '5', 'for': NODE_B})
        self.assertNotIn('body', self.fetch({'since': '0', 'for': NODE_B}, headers)[1])

    def test_compromised_key_gets_redacted(self):
        self.readers.add(NODE_B + '#key-1', ed25519.public_key(SECRET_B),
                         compromised='2026-09-28T00:00:00Z')
        query = {'since': '0', 'for': NODE_B}
        self.assertNotIn('body', self.fetch(query, self.signed(NODE_B, SECRET_B, query))[1])

    def test_redacted_answer_still_verifies(self):
        events = self.fetch({'since': '0', 'for': NODE_B})
        self.assertEqual(log.check_chain(events, self.a.keyring(), NOW), log.OK)

    def test_limit_capped(self):
        for minute in range(2, 12):
            self.a.append('2026-09-28T10:%02d:00Z' % minute, 'catalog.offer.published',
                          NODE_A + '/offer/%d' % minute, {})
        self.assertEqual(len(self.fetch({'since': '0', 'limit': '5'})), 5)
        self.assertEqual(len(self.fetch({'since': '0', 'limit': '0'})), 1)
        self.assertEqual(len(self.fetch({'since': '0', 'limit': '100000'})), 12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
