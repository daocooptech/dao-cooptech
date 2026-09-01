# -*- coding: utf-8 -*-
"""Тесты снимков состояния и двусторонних отзывов.

Запуск:  python federation/ref/test_protocol_gaps.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from federation.ref import ed25519, log, review   # noqa: E402

NOW = '2026-09-30T00:00:00Z'
NODE_A = 'did:web:coop-borozda.example.ru'
NODE_B = 'did:web:artel-severnyy-les.example.ru'
SECRET_A = bytes(range(32))
SECRET_B = bytes(range(32, 64))
DEAL = NODE_A + '/deal/СД-2026-000101'


class Snapshots(unittest.TestCase):
    """Узел после долгого офлайна догоняет снимком, а не историей с нуля."""

    def setUp(self):
        self.log = log.Log(NODE_A, NODE_A + '#key-1', SECRET_A)
        self.ring = self.log.keyring()
        for i in range(10):
            self.log.append('2026-09-0%dT10:00:00Z' % (i % 9 + 1),
                            'catalog.offer.published', NODE_A + '/offer/%d' % i,
                            {'название': 'Мука в/с', 'номер': i})
        self.state = {'offers': 10, 'balance': {'amount': '0.00', 'currency': 'RUB'}}

    def test_full_log_before_pruning(self):
        self.assertEqual(len(self.log.since(0, limit=100)), 10)

    def test_request_below_horizon_is_refused(self):
        self.log.prune(6)
        with self.assertRaises(log.TooOld) as caught:
            self.log.since(0)
        self.assertEqual(caught.exception.horizon, 6)

    def test_tail_after_horizon_still_served(self):
        self.log.prune(6)
        self.assertEqual([e['seq'] for e in self.log.since(6, limit=100)], [6, 7, 8, 9])

    def test_snapshot_verifies(self):
        snap = self.log.snapshot_at(5, self.state, NOW)
        self.assertEqual(log.check_snapshot(snap, self.state, self.ring), log.OK)

    def test_snapshot_state_must_match_its_hash(self):
        snap = self.log.snapshot_at(5, self.state, NOW)
        with self.assertRaises(log.Invalid):
            log.check_snapshot(snap, {'offers': 99}, self.ring)

    def test_forged_snapshot_rejected(self):
        snap = self.log.snapshot_at(5, self.state, NOW)
        snap['seq'] = 9
        with self.assertRaises(log.Invalid):
            log.check_snapshot(snap, self.state, self.ring)

    def test_snapshot_from_another_node_rejected(self):
        snap = self.log.snapshot_at(5, self.state, NOW)
        snap['kid'] = NODE_B + '#key-1'
        with self.assertRaises(log.Invalid):
            log.check_snapshot(snap, self.state, self.ring)

    def test_catching_up_from_snapshot(self):
        """Полный сценарий: снимок плюс хвост дают проверяемое состояние."""
        snap = self.log.snapshot_at(5, self.state, NOW)
        self.log.prune(6)
        log.check_snapshot(snap, self.state, self.ring)
        tail = self.log.since(snap['seq'] + 1, limit=100)
        self.assertEqual(log.check_chain(tail, self.ring, NOW, after=snap), log.OK)
        self.assertEqual([e['seq'] for e in tail], [6, 7, 8, 9])

    def test_tail_from_wrong_place_does_not_stick(self):
        snap = self.log.snapshot_at(5, self.state, NOW)
        tail = self.log.since(8, limit=100)
        with self.assertRaises(log.Invalid):
            log.check_chain(tail, self.ring, NOW, after=snap)

    def test_snapshot_needs_an_existing_event(self):
        with self.assertRaises(log.Invalid):
            self.log.snapshot_at(99, self.state, NOW)


class Reviews(unittest.TestCase):
    """Одновременное раскрытие: подстроить свою оценку под чужую нельзя."""

    PARTIES = (NODE_A, NODE_B)
    SALT_A = 'соль-первой-стороны-0001'
    SALT_B = 'соль-второй-стороны-0002'

    def commits(self, *who):
        out = []
        if NODE_A in who:
            out.append(review.commit(DEAL, NODE_A, 5, 'Всё в срок, брак не встретился', self.SALT_A))
        if NODE_B in who:
            out.append(review.commit(DEAL, NODE_B, 3, 'Оплата пришла с задержкой на неделю', self.SALT_B))
        return out

    def reveals(self, *who):
        out = []
        if NODE_A in who:
            out.append(review.reveal(DEAL, NODE_A, 5, 'Всё в срок, брак не встретился', self.SALT_A))
        if NODE_B in who:
            out.append(review.reveal(DEAL, NODE_B, 3, 'Оплата пришла с задержкой на неделю', self.SALT_B))
        return out

    def test_commitment_hides_the_rating(self):
        one = review.commit(DEAL, NODE_A, 5, 'отлично', 'соль-подлиннее-0001')
        two = review.commit(DEAL, NODE_A, 1, 'ужасно', 'соль-подлиннее-0001')
        self.assertNotEqual(one['hash'], two['hash'])
        self.assertNotIn('rating', one)
        self.assertNotIn('text', one)

    def test_salt_is_required(self):
        with self.assertRaises(review.Invalid):
            review.commit(DEAL, NODE_A, 5, 'отлично', 'соль')

    def test_rating_range(self):
        with self.assertRaises(review.Invalid):
            review.commit(DEAL, NODE_A, 0, 'x', 'соль-подлиннее-0001')

    def test_one_commitment_keeps_everything_closed(self):
        self.assertEqual(
            review.disclosure(DEAL, self.PARTIES, self.commits(NODE_A), []),
            review.CLOSED)

    def test_one_reveal_shows_nothing(self):
        state = review.disclosure(DEAL, self.PARTIES,
                                  self.commits(NODE_A, NODE_B), self.reveals(NODE_A))
        self.assertEqual(state, review.AWAITING)
        self.assertEqual(review.visible(DEAL, self.PARTIES,
                                        self.commits(NODE_A, NODE_B),
                                        self.reveals(NODE_A)), [])

    def test_both_reveals_open_together(self):
        shown = review.visible(DEAL, self.PARTIES,
                               self.commits(NODE_A, NODE_B), self.reveals(NODE_A, NODE_B))
        self.assertEqual(len(shown), 2)
        self.assertEqual(sorted(r['rating'] for r in shown), [3, 5])

    def test_cannot_change_review_after_seeing_the_other(self):
        """Главное свойство схемы: обязательство фиксирует оценку заранее."""
        commitments = self.commits(NODE_A, NODE_B)
        # Первая сторона увидела, что её оценили на тройку, и хочет ответить тем же.
        revenge = review.reveal(DEAL, NODE_A, 1, 'Сам виноват', self.SALT_A)
        with self.assertRaises(review.Invalid):
            review.visible(DEAL, self.PARTIES, commitments,
                           [revenge] + self.reveals(NODE_B))

    def test_reveal_without_commitment_rejected(self):
        with self.assertRaises(review.Invalid):
            review.visible(DEAL, self.PARTIES,
                           self.commits(NODE_A), self.reveals(NODE_A, NODE_B),
                           after_deadline=True)

    def test_deadline_opens_what_was_revealed(self):
        """Молчание второй стороны не держит чужой отзыв закрытым вечно."""
        shown = review.visible(DEAL, self.PARTIES,
                               self.commits(NODE_A, NODE_B), self.reveals(NODE_A),
                               after_deadline=True)
        self.assertEqual(len(shown), 1)
        self.assertEqual(shown[0]['author'], NODE_A)

    def test_outsider_review_ignored(self):
        outsider = review.commit(DEAL, 'did:web:chuzhoy.example.ru', 5, 'ок',
                                 'соль-постороннего-01')
        self.assertEqual(
            review.disclosure(DEAL, self.PARTIES,
                              self.commits(NODE_A) + [outsider], []),
            review.CLOSED)


if __name__ == '__main__':
    unittest.main(verbosity=2)
