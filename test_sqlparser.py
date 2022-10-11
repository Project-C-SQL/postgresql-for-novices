import pytest
import sqlparser

def test_parse_one():
    IMPOSSIBLE_STATEMENT = \
"""
SELECT * FROM orders
    WHERE order_total_eur = 0 AND order_total_eur = 100;"""

    CHECK_CONSTRAINT = \
"""
CREATE TABLE dummy (
    hype CHAR(1) CHECK (hype = ANY (ARRAY['X'::bpchar, 'Y'::bpchar]))
    );"""

    parser = sqlparser.SqlParser()

    try:
        statement = IMPOSSIBLE_STATEMENT
        parsed = parser.parse_one(statement)
    except Exception as e:
        assert False, f"exception: {e}"

    try:
        statement = CHECK_CONSTRAINT
        parsed = parser.parse_one(statement)
    except Exception as e:
        assert False, f"exception: {e}"

def test_parse():
    IMPOSSIBLE_STATEMENT = \
"""
SELECT * FROM orders
    WHERE order_total_eur = 0 AND order_total_eur = 100;"""

    CHECK_CONSTRAINT = \
"""
CREATE TABLE dummy (
    hype CHAR(1) CHECK (hype = ANY (ARRAY['X'::bpchar, 'Y'::bpchar]))
    );"""

    parser = sqlparser.SqlParser()

    try:
        statement = IMPOSSIBLE_STATEMENT
        parsed = parser.parse(statement)[0]
    except Exception as e:
        assert False, f"exception: {e}"

    try:
        statement = CHECK_CONSTRAINT
        parsed = parser.parse(statement)[0]
    except Exception as e:
        assert False, f"exception: {e}"
