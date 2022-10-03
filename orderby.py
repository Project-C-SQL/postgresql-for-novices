import sys
import subprocess
import sqlglot
import sqlparser
from pprint import pprint
from myutils import putsep

def has_subquery_order_by(sql: sqlglot.exp.Expression, qep: str) -> bool:
    """
    Does not use the qep so far.
    """

    # First strips parentheses
    tmp = sql.unnest()

    # sqlglot classifies top level parenthesis as subquery
    # We need to strip those away otherwise statements like:
    # '(SELECT * FROM table t ORDER BY t.id);' return True
    if (type(tmp) == sqlglot.exp.Subquery):
        tmp = tmp.unnest()

    # Creates a deep copy
    unnested = sqlglot.parse_one(tmp.sql())

    # Except and Intersect are subclass of Union
    if isinstance(unnested, sqlglot.exp.Union):
        return (has_subquery_order_by(unnested.left, qep) or
                has_subquery_order_by(unnested.right, qep))

    subqueries = \
        filter(lambda x: x.parent != None, unnested.find_all(sqlglot.exp.Select))

    return any([subquery.find(sqlglot.exp.Order) for subquery in subqueries])


STATEMENT_WITHOUT_OUTER_ORDER = \
    f"""
SELECT *
FROM customers c
WHERE EXISTS (
    SELECT *
    FROM orders o
    WHERE c.customer_id = o.customer_id
    ORDER BY o.customer_id
    );
"""

STATEMENT_OUTER_ORDER_WITHOUT_INNER_ORDER = \
    f"""
SELECT *
FROM customers c
WHERE EXISTS (
    SELECT *
    FROM orders o
    WHERE c.customer_id = o.customer_id
    )
ORDER BY c.customer_id;
"""

STATEMENT_OUTER_ORDER_WITH_INNER_ORDER = \
    f"""
SELECT *
FROM customers c
WHERE EXISTS (
    SELECT *
    FROM orders o
    WHERE c.customer_id = o.customer_id
    ORDER BY o.customer_id
    )
ORDER BY c.customer_id;
"""

STATEMENT_MULTIPLE_INNER_ORDERS = \
    f"""
SELECT *
FROM customers c
WHERE EXISTS (
    SELECT *
    FROM orders o
    WHERE c.customer_id = o.customer_id
    ORDER BY o.customer_id
    ) OR EXISTS (
    SELECT *
    FROM orders o
    WHERE c.customer_id = o.customer_id
    ORDER BY o.customer_id
    );
"""

STATEMENT_NESTED_SUBQUERY_INNER_ORDER = \
    f"""
SELECT *
FROM customers c
WHERE EXISTS (
    SELECT *
    FROM (SELECT *
          FROM orders o2
          ORDER BY o2.customer_id) AS o
    WHERE c.customer_id = o.customer_id
    );
"""

STATEMENT_SIMPLE = \
    f"""
SELECT *
FROM customers c
ORDER BY c.customer_id
"""

STATEMENT_REDUNDANT_PARENTHESES = \
    f"""
((((
SELECT *
FROM customers c
ORDER BY c.customer_id
))));
"""

STATEMENT_UNION = \
    f"""
SELECT c.customer_id
FROM customers c
UNION
SELECT o.customer_id
FROM orders o
ORDER BY customer_id;
"""

STATEMENT_NESTED_UNION = \
    f"""
SELECT c.customer_id
FROM customers c
UNION
(SELECT o.customer_id
 FROM orders o
 WHERE o.customer_id < 20
 UNION
 SELECT o.customer_id
 FROM orders o
 WHERE o.customer_id > 80
)
ORDER BY customer_id;
"""

STATEMENT_EXCEPT = \
    f"""
SELECT c.customer_id
FROM customers c
EXCEPT
SELECT o.customer_id
FROM orders o
ORDER BY customer_id;
"""

STATEMENT_INTERSECT = \
    f"""
SELECT c.customer_id
FROM customers c
INTERSECT
SELECT o.customer_id
FROM orders o
ORDER BY customer_id;
"""

STATEMENT_COMPLEX = \
    f"""
(((
SELECT c.customer_id
FROM customers c
UNION
(SELECT o.customer_id
 FROM orders o
 WHERE o.customer_id < 20 AND
    EXISTS (
        SELECT *
        FROM orders o2
        WHERE o2.customer_id = 50
        ORDER BY o2.customer_id
    )
 UNION
 SELECT o.customer_id
 FROM orders o
 WHERE o.customer_id > 80
)
ORDER BY customer_id
)));
"""


def _test(expected: bool, sql_statement: str, db_name: str):
    # TODO: call qep parser module here instead
    qep = subprocess.check_output(["psql", "-X", "-d", db_name, "-c",
                                   "EXPLAIN ANALYZE " + sql_statement])
    qep = bytes.decode(qep)

    parsed_sql = sqlparser.parse(sql_statement)
    result = has_subquery_order_by(parsed_sql, qep)
    print(f"expected: {expected}, result: {str(result)}")
    if expected != result:
        print(parsed_sql)


USAGE = "usage: orderby.py <db_name>"


def main():
    if len(sys.argv) != 2:
        print(USAGE, file=sys.stderr)
        exit(1)

    db_name = str(sys.argv[1])

    _test(True, STATEMENT_WITHOUT_OUTER_ORDER, db_name)
    _test(False, STATEMENT_OUTER_ORDER_WITHOUT_INNER_ORDER, db_name)
    _test(True, STATEMENT_OUTER_ORDER_WITH_INNER_ORDER, db_name)
    _test(True, STATEMENT_MULTIPLE_INNER_ORDERS, db_name)
    _test(True, STATEMENT_NESTED_SUBQUERY_INNER_ORDER, db_name)
    _test(False, STATEMENT_SIMPLE, db_name)
    _test(False, STATEMENT_REDUNDANT_PARENTHESES, db_name)
    _test(False, STATEMENT_UNION, db_name)
    _test(False, STATEMENT_NESTED_UNION, db_name)
    _test(False, STATEMENT_EXCEPT, db_name)
    _test(False, STATEMENT_INTERSECT, db_name)
    _test(True, STATEMENT_COMPLEX, db_name)

if __name__ == "__main__":
    main()
