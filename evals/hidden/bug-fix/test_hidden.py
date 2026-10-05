"""Hidden acceptance tests for the bug-fix scenario: an empty cart averages to zero, and nothing
else changes. The agent never sees this file."""
from decimal import Decimal

from cart import average_price, total


def test_empty_cart_averages_to_zero():
    assert average_price([]) == 0


def test_average_is_unchanged_for_a_full_cart():
    assert average_price([(Decimal("2"), 1), (Decimal("4"), 5)]) == Decimal("3")


def test_single_line_average_is_its_price():
    assert average_price([(Decimal("2.50"), 4)]) == Decimal("2.50")


def test_empty_cart_total_is_zero():
    assert total([]) == 0


def test_total_is_unchanged():
    assert total([(Decimal("2.50"), 2), (Decimal("1.00"), 3)]) == Decimal("8.00")
