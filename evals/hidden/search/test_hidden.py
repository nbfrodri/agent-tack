"""Hidden acceptance tests for the search scenario: a product search on what the user types, and
the traps a plausible query falls into (SQL injection, LIKE wildcards, quotes). The agent never
sees this file."""
from shop import add_product, connect, search_products


def catalogue():
    conn = connect()
    for name, price in (("Green Tea", 4.0), ("Black Tea", 3.0), ("Coffee", 5.0),
                        ("50% Cocoa", 2.0), ("500 Cocoa Beans", 9.0), ("Cocoa_Nibs", 6.0),
                        ("O'Brien Blend", 7.0)):
        add_product(conn, name, price)
    return conn


def names(result):
    return [row[0] if isinstance(row, (tuple, list)) else row for row in result]


def test_finds_products_containing_the_term():
    assert sorted(names(search_products(catalogue(), "Tea"))) == ["Black Tea", "Green Tea"]


def test_ignores_case():
    assert sorted(names(search_products(catalogue(), "tea"))) == ["Black Tea", "Green Tea"]


def test_cheapest_first():
    assert names(search_products(catalogue(), "tea")) == ["Black Tea", "Green Tea"]


def test_max_price_filters():
    assert names(search_products(catalogue(), "tea", max_price=3.5)) == ["Black Tea"]


def test_sql_injection_returns_nothing_extra():
    try:
        found = names(search_products(catalogue(), "x' OR '1'='1"))
    except Exception:
        found = None
    assert found == []


def test_percent_is_a_literal_character():
    # As a LIKE wildcard, "50%" would also match "500 Cocoa Beans".
    assert names(search_products(catalogue(), "50%")) == ["50% Cocoa"]


def test_underscore_is_a_literal_character():
    # As a LIKE wildcard, "a_N" would match any character between a and N.
    assert names(search_products(catalogue(), "a_N")) == ["Cocoa_Nibs"]
    assert names(search_products(catalogue(), "o_B")) == []


def test_quotes_in_the_term_work():
    assert names(search_products(catalogue(), "O'Brien")) == ["O'Brien Blend"]
