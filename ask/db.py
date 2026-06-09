"""Read-only DuckDB access with a query guardrail.

Two layers of protection against anything that is not a read:
  1. `check_safe` rejects multi-statement input, non-SELECT/WITH queries, and
     any forbidden (write/DDL) keyword before the query is ever run.
  2. The connection itself is opened `read_only=True`, so even a query that
     slipped past the check cannot modify the database.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import duckdb

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma|"
    r"truncate|replace|merge|grant|revoke|export|import|install|load|vacuum|call)\b",
    re.IGNORECASE,
)


class UnsafeQueryError(ValueError):
    """Raised when a query is not a single, read-only SELECT."""


@dataclass
class QueryResult:
    columns: list
    rows: list
    sql: str


class Warehouse:
    def __init__(self, path: str):
        self.path = path

    def _connect(self):
        return duckdb.connect(self.path, read_only=True)

    def list_tables(self) -> list:
        con = self._connect()
        try:
            return [r[0] for r in con.execute(
                "select table_name from information_schema.tables "
                "where table_schema = 'main' order by table_name").fetchall()]
        finally:
            con.close()

    def columns(self, table: str) -> list:
        con = self._connect()
        try:
            return [(r[0], r[1]) for r in con.execute(
                "select column_name, data_type from information_schema.columns "
                "where table_name = ? order by ordinal_position", [table]).fetchall()]
        finally:
            con.close()

    @staticmethod
    def check_safe(sql: str) -> None:
        s = sql.strip().rstrip(";").strip()
        if not s:
            raise UnsafeQueryError("Empty query.")
        if ";" in s:
            raise UnsafeQueryError("Only a single statement is allowed.")
        low = s.lower()
        if not (low.startswith("select") or low.startswith("with")):
            raise UnsafeQueryError("Only read-only SELECT/WITH queries are allowed.")
        if _FORBIDDEN.search(s):
            raise UnsafeQueryError("Query contains a forbidden (non-read-only) keyword.")

    def run(self, sql: str, max_rows: int = 200) -> QueryResult:
        self.check_safe(sql)
        s = sql.strip().rstrip(";").strip()
        if "limit" not in s.lower():
            s = f"{s}\nlimit {max_rows}"
        con = self._connect()
        try:
            cur = con.execute(s)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        finally:
            con.close()
        return QueryResult(columns=cols, rows=rows, sql=s)
