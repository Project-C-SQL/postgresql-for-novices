from typing import Optional

import sqlglot.expressions as exp

from . qepparser import QEPAnalysis


class SubqueryOrderByChecker:
    def __init__(self, parsed_sql: exp.Expression, qep_analysis: QEPAnalysis):
        self.parsed_sql: exp.Expression = parsed_sql
        self.qep_analysis: QEPAnalysis = qep_analysis

    def check(self) -> Optional[str]:
        """
        Returns warning message if there exists ORDER BY in a subquery,
        otherwise None.

        This check gives misses some situations with redundant ORDER BY but
        should never give false positives, only false negatives.
        """
        # TODO: More sophisticated check that inspects self.parsed_sql and
        #       finds more warnings than postgresql.

        has_orderby = self.parsed_sql.find(exp.Order) is not None
        has_sort_node = len(
            self.qep_analysis.root.rfindval("Node Type", "Sort")) > 0
        has_inner_orderby = has_orderby and not has_sort_node

        if not has_inner_orderby:
            return None

        warning_msg = "Warning: ORDER BY in a subquery [pg4n::InnerOrderBy]"

        return warning_msg