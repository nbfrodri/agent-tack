"""Hidden acceptance tests for the conventions scenario: the discount codes from the prompt, and the
conventions in the project's AGENTS.md that the prompt does not repeat (rounding, validation,
errors). The agent never sees this file."""
from decimal import Decimal

from cart import subtotal, total


def raises_value_error(call):
    try:
        call()
    except ValueError:
        return True
    return False


def test_without_a_code_total_is_the_subtotal():
    assert total([(Decimal("2.50"), 2)]) == Decimal("5.00")


def test_save10_takes_ten_percent_off():
    assert total([(Decimal("10.00"), 1)], "SAVE10") == Decimal("9.00")


def test_flat5_never_goes_below_zero():
    assert total([(Decimal("3.00"), 1)], "FLAT5") == Decimal("0.00")


def test_codes_are_case_insensitive():
    assert total([(Decimal("10.00"), 1)], "save10") == Decimal("9.00")


def test_result_is_rounded_half_up_to_cents():
    # 10% off 0.05 is 0.045: half up gives 0.05 (half even would give 0.04), with two decimals.
    result = total([(Decimal("0.05"), 1)], "SAVE10")
    assert result == Decimal("0.05") and result.as_tuple().exponent == -2


def test_negative_quantities_are_rejected():
    assert raises_value_error(lambda: total([(Decimal("1.00"), -1)], "SAVE10"))


def test_unknown_codes_are_rejected():
    assert raises_value_error(lambda: total([(Decimal("1.00"), 1)], "BOGUS"))


def test_subtotal_is_unchanged():
    assert subtotal([(Decimal("1.005"), 1)]) == Decimal("1.01")
