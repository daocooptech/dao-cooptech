# -*- coding: utf-8 -*-
"""Все тесты справочной реализации одной командой.

    python federation/ref/run_tests.py

Отдельные наборы запускаются и сами по себе — test_federation.py (журнал,
конверт, подпись, вымарывание, ключи, состояние сделки) и test_line.py
(линия взаимного обязательства, раунд взаимозачёта).
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(os.path.abspath(__file__)),
                            pattern='test_*.py', top_level_dir=ROOT)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
