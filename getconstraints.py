import sys
import subprocess
import sqlparser
import sqlglot
from typing import NoReturn
from pprint import pprint
from dataclasses import dataclass
import re


def get_check_constraints(db_name: str,
                          table_name: str) -> list[sqlglot.exp.Constraint]:
    """
    Requires that 'db_name' is valid and that a table 'table_name' exists in it.
    """

    check_constraints = _get_check_constraints(db_name, table_name)
    type_names = _get_column_types(db_name, table_name,
                                   [x.column for x in check_constraints])

#     # sqlparser cannot parse sql statement fragments so we have to wrap it in
#     # a valid dummy sql statement.
    dummy_create_table_columns = ""
    assert (len(type_names) == len(check_constraints))
    i = 0
    while i < len(check_constraints):
        col = f"    {check_constraints[i].column} {type_names[i]} " \
              f"{check_constraints[i].constraint},\n"
        dummy_create_table_columns += col
        i += 1

    dummy_create_table_statement = \
        "CREATE TABLE dummy (\n" + dummy_create_table_columns + ");"
    output = sqlparser.parse(dummy_create_table_statement)
    # pprint(output)
    constraints = []
    columndefs = output.find_all(sqlglot.exp.ColumnDef)
    for columndef in columndefs:
        constraint = columndef.find(sqlglot.exp.ColumnConstraint)
        constraints.append(constraint)

    return constraints


@dataclass(frozen=True)
class CheckConstraint:
    column: str
    constraint: str


def _get_check_constraints(db_name: str,
                           table_name: str) -> list[CheckConstraint]:
    # This statement is part of the output of running '\d <table_name>' inside
    # psql -E (--echo-hidden)
    # The r.contype = 'c' selects only check constraints.
    statement = \
        f"""
SELECT conname,
       pg_catalog.pg_get_constraintdef(r.oid, true) AS condef,
       conrelid::pg_catalog.regclass
FROM pg_catalog.pg_constraint AS r
WHERE r.contype = 'c' AND conparentid = 0 AND
      conname LIKE '{table_name}_%_check'
ORDER BY conname;"""

    out = subprocess.check_output(["psql", "-A", "-t", "-X", "-d", db_name, "-c",
                                   statement])

    rows = bytes.decode(out).rstrip('\n').split('\n')
    check_constraints = []

    for row in rows:
        fields = row.split('|')
        column = fields[0][fields[0].find('_')+1:fields[0].rfind('_')]
        constraint = fields[1]
        check_constraints.append(CheckConstraint(column, constraint))

    return check_constraints


def _convert_from_internal_types(type_names: list[str]) -> list[str]:
    """
    Postgresql has internal type names such as: character or character(x).
    sqlglot can only parse the types in the form they are declared (atleast in
    column definitions inside CREATE TABLE) like: CHAR or CHAR(x).
    This function converts from the internal to the declared form.
    """

    converted_types = []
    character_matcher = re.compile(r'^(?:character|char)\((\d+)\)$')
    varchar_matcher = re.compile(
        r'^(?:(?:character varying)|varchar)\((\d+)\)$')

    for type_name in type_names:
        if type_name == "character":
            converted_types.append("CHAR")
        elif type_name == "char":
            converted_types.append("CHAR")
        elif match := character_matcher.match(type_name):
            converted_types.append(f"CHAR({match.group(1)})")
        elif match := varchar_matcher.match(type_name):
            converted_types.append(f"VARCHAR({match.group(1)})")

    return converted_types


def _get_column_types(db_name: str, table_name: str,
                      columns: list[str]) -> list[str]:
    # sql adapted from: https://stackoverflow.com/a/20194807/13540518
    column_type_statement_prefix = \
        f"""
SELECT
    pg_catalog.format_type(a.atttypid, a.atttypmod) AS "data_type"
FROM
    pg_catalog.pg_attribute a
WHERE
    a.attnum > 0
    AND NOT a.attisdropped
    AND a.attrelid = (
        SELECT c.oid
            FROM pg_catalog.pg_class c
            LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = '{table_name}'
                AND pg_catalog.pg_table_is_visible(c.oid)
                AND a.attname IN ("""

    if len(columns) == 0:
        return ""

    in_condition = ""
    for col in columns[:-1]:
        in_condition += f"'{col}', "
    in_condition += f"'{columns[-1]}')\n    );"
    column_type_statement = column_type_statement_prefix + in_condition

    output = subprocess.check_output(["psql", "-A", "-t", "-X", "-d",
                                      db_name, "-c", column_type_statement])
    type_names = bytes.decode(output).rstrip('\n').split('\n')
    parseable_type_names = _convert_from_internal_types(type_names)

    return parseable_type_names


def _die(msg: str) -> NoReturn:
    print(msg, file=sys.stderr)
    exit(1)


USAGE = "usage: getschema <dbname>"


def main():
    if (len(sys.argv) != 2):
        _die(USAGE)
    db_name = sys.argv[1]
    table_name = "customers"

    constraints = get_check_constraints(db_name, table_name)


if __name__ == "__main__":
    main()
