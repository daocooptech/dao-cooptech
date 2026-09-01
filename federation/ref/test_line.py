# -*- coding: utf-8 -*-
"""Тесты линии взаимного обязательства и раунда взаимозачёта.

Запуск:  python federation/ref/test_line.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from federation.ref import ed25519, line   # noqa: E402

A = 'did:web:coop-borozda.example.ru'
B = 'did:web:artel-severnyy-les.example.ru'
C = 'did:web:pekarnya-zerno.example.ru'
D = 'did:web:storonniy.example.ru'

SECRETS = {A: bytes(range(32)), B: bytes(range(32, 64)),
           C: bytes(range(64, 96)), D: bytes(range(96, 128))}
KEYS = {who: ed25519.public_key(secret) for who, secret in SECRETS.items()}


def signed(st, *who):
    for one in who:
        st = line.sign(st, one, SECRETS[one])
    return st


class LineIdentity(unittest.TestCase):

    def test_identifier_does_not_depend_on_who_opened(self):
        self.assertEqual(line.line_id(A, B), line.line_id(B, A))

    def test_line_with_self_rejected(self):
        with self.assertRaises(line.Invalid):
            line.line_id(A, A)

    def test_amount_must_be_a_string(self):
        with self.assertRaises(line.Invalid):
            line.state(line.line_id(A, B), 1, None,
                       {'amount': 150000.0, 'currency': 'RUB'}, 'сделка', '2026-09-01T10:00:00Z')

    def test_currency_must_be_iso(self):
        with self.assertRaises(line.Invalid):
            line.state(line.line_id(A, B), 1, None,
                       {'amount': '1.00', 'currency': 'токен'}, 'сделка', '2026-09-01T10:00:00Z')


class TwoSignatures(unittest.TestCase):
    """Обязательство действительно только при двух подписях."""

    def setUp(self):
        self.line = line.line_id(A, B)
        self.st = line.state(self.line, 1, None, line.money('150000.00'),
                             A + '/deal/СД-2026-000101', '2026-09-01T10:00:00Z')

    def test_one_signature_is_not_enough(self):
        with self.assertRaises(line.Invalid):
            line.check_state(signed(self.st, A), KEYS)

    def test_two_signatures_are_enough(self):
        self.assertTrue(line.check_state(signed(self.st, A, B), KEYS))

    def test_order_of_signing_does_not_matter(self):
        self.assertTrue(line.check_state(signed(self.st, B, A), KEYS))

    def test_third_party_signature_rejected(self):
        """Посторонний подписывает что угодно — на линию это не влияет."""
        with self.assertRaises(line.Invalid):
            line.check_state(signed(self.st, A, B, D), KEYS)

    def test_one_side_cannot_sign_for_the_other(self):
        """Подделать чужую подпись нельзя: проверка идёт по ключу стороны."""
        forged = signed(self.st, A)
        forged['sigs'][B] = forged['sigs'][A]
        with self.assertRaises(line.Invalid):
            line.check_state(forged, KEYS)

    def test_changing_amount_after_signing_breaks_it(self):
        st = signed(self.st, A, B)
        st['balance'] = line.money('15000.00')
        with self.assertRaises(line.Invalid):
            line.check_state(st, KEYS)


class Chain(unittest.TestCase):

    def setUp(self):
        self.line = line.line_id(A, B)
        first = signed(line.state(self.line, 1, None, line.money('150000.00'),
                                  'сделка 101', '2026-09-01T10:00:00Z'), A, B)
        second = signed(line.state(self.line, 2, line.state_id(first), line.money('90000.00'),
                                   'частичная оплата', '2026-09-05T10:00:00Z'), A, B)
        third = signed(line.state(self.line, 3, line.state_id(second), line.money('-20000.00'),
                                  'встречная поставка', '2026-09-10T10:00:00Z'), A, B)
        self.states = [first, second, third]

    def test_chain_verifies(self):
        self.assertTrue(line.check_line(self.states, KEYS))

    def test_removed_state_breaks_chain(self):
        with self.assertRaises(line.Invalid):
            line.check_line([self.states[0], self.states[2]], KEYS)

    def test_first_state_has_no_prev(self):
        self.assertIsNone(self.states[0]['prev'])
        with self.assertRaises(line.Invalid):
            line.state(self.line, 1, 'что-то', line.money('1.00'), 'x', '2026-09-01T10:00:00Z')

    def test_balance_flips_sides(self):
        """Должник — свойство момента, а не участника."""
        first, second = line.parties(self.line)
        self.assertGreater(line.balance_of(self.states[0], first), 0)
        self.assertLess(line.balance_of(self.states[2], first), 0)
        self.assertGreater(line.balance_of(self.states[2], second), 0)

    def test_outsider_has_no_position(self):
        with self.assertRaises(line.Invalid):
            line.balance_of(self.states[0], D)


class Fork(unittest.TestCase):
    """Форк нельзя предотвратить, но можно обнаружить с доказательством."""

    def test_two_states_with_same_version_detected(self):
        ln = line.line_id(A, B)
        honest = signed(line.state(ln, 1, None, line.money('150000.00'),
                                   'сделка 101', '2026-09-01T10:00:00Z'), A, B)
        forged = signed(line.state(ln, 1, None, line.money('15000.00'),
                                   'сделка 101', '2026-09-01T10:00:00Z'), A, B)
        fork = line.find_fork([honest, forged])
        self.assertIsNotNone(fork)
        # Обе записи подписаны обеими сторонами — это и есть доказательство.
        self.assertTrue(line.check_state(fork[0], KEYS))
        self.assertTrue(line.check_state(fork[1], KEYS))

    def test_honest_chain_has_no_fork(self):
        ln = line.line_id(A, B)
        first = signed(line.state(ln, 1, None, line.money('1.00'), 'x',
                                  '2026-09-01T10:00:00Z'), A, B)
        second = signed(line.state(ln, 2, line.state_id(first), line.money('2.00'), 'y',
                                   '2026-09-02T10:00:00Z'), A, B)
        self.assertIsNone(line.find_fork([first, second]))


class ClearingRound(unittest.TestCase):
    """Круг A→B→C→A гасится встречно, но только по подписям всех."""

    def setUp(self):
        self.rnd = line.round_(
            coordinator=A,
            participants=[A, B, C],
            entries=[
                {'debtor': A, 'creditor': B, 'amount': line.money('50000.00')},
                {'debtor': B, 'creditor': C, 'amount': line.money('50000.00')},
                {'debtor': C, 'creditor': A, 'amount': line.money('50000.00')},
            ],
            deadline='2026-09-30T00:00:00Z')

    def sigs(self, *who):
        return [line.sign_round(self.rnd, one, SECRETS[one]) for one in who]

    def test_round_is_neutral(self):
        self.assertTrue(line.check_round(self.rnd))

    def test_unbalanced_round_rejected(self):
        """Несбалансированная таблица — скрытый перевод долга, а не зачёт."""
        bad = line.round_(A, [A, B], [
            {'debtor': A, 'creditor': B, 'amount': line.money('50000.00')},
        ], '2026-09-30T00:00:00Z')
        with self.assertRaises(line.Invalid):
            line.check_round(bad)

    def test_mixed_currencies_rejected(self):
        """Требования в разных валютах не однородны, зачесть их нельзя."""
        with self.assertRaises(line.Invalid):
            line.round_(A, [A, B], [
                {'debtor': A, 'creditor': B, 'amount': line.money('1.00', 'USD')},
            ], '2026-09-30T00:00:00Z')

    def test_outsider_cannot_be_in_entries(self):
        with self.assertRaises(line.Invalid):
            line.round_(A, [A, B], [
                {'debtor': A, 'creditor': D, 'amount': line.money('1.00')},
            ], '2026-09-30T00:00:00Z')

    def test_incomplete_set_blocks_application(self):
        with self.assertRaises(line.Invalid):
            line.apply_round(self.rnd, self.sigs(A, B), KEYS, {})
        self.assertEqual(line.collected(self.rnd, self.sigs(A, B), KEYS), [C])

    def test_coordinator_alone_cannot_apply(self):
        """Координатор — нотариус раунда, а не банк."""
        with self.assertRaises(line.Invalid):
            line.apply_round(self.rnd, self.sigs(A), KEYS, {})

    def test_full_set_applies(self):
        balances = {line.line_id(A, B): '-50000.00',
                    line.line_id(B, C): '-50000.00',
                    line.line_id(C, A): '-50000.00'}
        # Приводим знаки к точке зрения первой стороны каждой линии.
        balances = {}
        for entry in self.rnd['entries']:
            ln = line.line_id(entry['debtor'], entry['creditor'])
            first, _ = line.parties(ln)
            balances[ln] = '50000.00' if entry['creditor'] == first else '-50000.00'
        result = line.apply_round(self.rnd, self.sigs(A, B, C), KEYS, balances)
        for value in result.values():
            self.assertEqual(value, '0.00')

    def test_round_id_is_stable(self):
        """Хэш таблицы не зависит от порядка ключей: по нему узлы узнают,
        что применяют один и тот же раунд, и не применяют его дважды."""
        same = dict(reversed(list(self.rnd.items())))
        self.assertEqual(line.round_id(self.rnd), line.round_id(same))

    def test_round_id_changes_with_the_table(self):
        changed = dict(self.rnd)
        changed['entries'] = [dict(e) for e in self.rnd['entries']]
        changed['entries'][0]['amount'] = line.money('50000.01')
        self.assertNotEqual(line.round_id(self.rnd), line.round_id(changed))

    def test_signature_under_another_table_does_not_count(self):
        """Подменить таблицу после сбора подписей нельзя."""
        other = line.round_(A, [A, B, C], [
            {'debtor': A, 'creditor': B, 'amount': line.money('10000.00')},
            {'debtor': B, 'creditor': C, 'amount': line.money('10000.00')},
            {'debtor': C, 'creditor': A, 'amount': line.money('10000.00')},
        ], '2026-09-30T00:00:00Z')
        stale = [line.sign_round(other, one, SECRETS[one]) for one in (A, B, C)]
        # Подписи собраны, но под другой таблицей — для нашего раунда их нет.
        self.assertEqual(line.collected(self.rnd, stale, KEYS), sorted([A, B, C]))
        with self.assertRaises(line.Invalid):
            line.apply_round(self.rnd, stale, KEYS, {})

    def test_outsider_signature_does_not_complete_the_set(self):
        outsider = line.sign_round(
            line.round_(A, [A, B, C, D], self.rnd['entries'] + [], '2026-09-30T00:00:00Z'),
            D, SECRETS[D])
        self.assertIn(C, line.collected(self.rnd, self.sigs(A, B) + [outsider], KEYS))


if __name__ == '__main__':
    unittest.main(verbosity=2)
