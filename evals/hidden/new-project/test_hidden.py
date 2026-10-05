"""Hidden acceptance tests for the new-project scenario: cart_total(items) applies a 10% discount
to a line of 10 or more units and 21% VAT. The agent never sees this file.
Prices go in as Decimal, or as float when the implementation only accepts floats; totals are
compared to the cent, so either rounding style passes."""
from decimal import Decimal

from cart import cart_total


def total_of(lines):
    try:
        return float(cart_total([(Decimal(str(price)), quantity) for price, quantity in lines]))
    except (TypeError, ValueError):
        return float(cart_total([(float(price), quantity) for price, quantity in lines]))


def close(value, expected):
    return abs(value - expected) < 0.011


def test_empty_cart_is_zero():
    assert close(total_of([]), 0)


def test_vat_is_added_below_the_discount():
    assert close(total_of([("5.00", 2)]), 12.10)


def test_nine_units_get_no_discount():
    assert close(total_of([("1.00", 9)]), 10.89)


def test_ten_units_get_the_discount():
    assert close(total_of([("1.00", 10)]), 10.89)


def test_eleven_units_get_the_discount():
    assert close(total_of([("1.00", 11)]), 11.979)


def test_the_discount_applies_per_line():
    assert close(total_of([("10.00", 10), ("3.00", 1)]), 112.53)
