"""
Tests for the money math in app/services/calculations.py.
These don't need a database or a server.
"""

from types import SimpleNamespace

import pytest

from app.services.calculations import (
    calculate_actual_profit,
    calculate_projected_profit,
    calculate_roi,
    calculate_total_expenses,
    calculate_total_investment,
)


def expenses(*amounts):
    return [SimpleNamespace(amount=a) for a in amounts]


def test_total_expenses_adds_every_expense():
    assert calculate_total_expenses(expenses(150, 350, 99.5)) == pytest.approx(599.5)


def test_total_expenses_is_zero_with_no_expenses():
    assert calculate_total_expenses([]) == 0


def test_total_investment_is_purchase_plus_expenses():
    assert calculate_total_investment(5000, expenses(150, 350)) == 5500


def test_projected_profit_uses_asking_price():
    assert calculate_projected_profit(5000, 8000, expenses(500)) == 2500


def test_projected_profit_can_be_negative():
    assert calculate_projected_profit(9000, 8000, expenses(500)) == -1500


def test_actual_profit_is_none_before_sale():
    assert calculate_actual_profit(5000, None, expenses(500)) is None


def test_actual_profit_after_sale():
    assert calculate_actual_profit(5000, 7800, expenses(500)) == 2300


def test_roi_is_none_before_sale():
    assert calculate_roi(5000, None, expenses(500)) is None


def test_roi_after_sale():
    # 2300 profit on 5500 invested
    assert calculate_roi(5000, 7800, expenses(500)) == pytest.approx(41.818181, rel=1e-5)


def test_roi_is_zero_when_nothing_invested():
    assert calculate_roi(0, 1000, []) == 0
