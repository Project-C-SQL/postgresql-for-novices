import sys
import sqlglot
from sqlglot.dialects.postgres import Postgres

class SqlParser:
    # Patches the postgres dialect to recognize bpchar
    Postgres.Tokenizer.KEYWORDS["BPCHAR"] = sqlglot.TokenType.CHAR

    def __init__(self):
        self.dialect = "postgres"

    def parse(self, sql: str) -> list[sqlglot.exp.Expression]:
        """
        Parses all the statements in 'sql'.
        'sql' should be a string of one or more postgresql statements (delimited by ';').
        The last ';' in 'sql' is optional.
        Throws sqlglot.ParseError on invalid sql.
        """

        return sqlglot.parse(sql, read=self.dialect)

    def parse_one(self, sql: str) -> sqlglot.exp.Expression:
        """
        Parses the first statement in 'sql'.
        Does not validate that 'sql' contains only 1 statement!
        'sql' should be a postgresql statement.
        The trailing ';' in 'sql' is optional.
        Throws sqlglot.ParseError on invalid sql.
        """

        return sqlglot.parse_one(sql, read=self.dialect)
