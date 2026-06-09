"""Orchestrates a question into a trustworthy answer.

Flow: match a curated skill -> otherwise ask the LLM for SQL -> validate the
SQL against the read-only guardrail -> execute -> return the SQL and the rows.
The SQL is always returned alongside the answer, so a result is never a black box.
"""
from __future__ import annotations

from dataclasses import dataclass

from .db import QueryResult, UnsafeQueryError, Warehouse
from .llm import LLMUnavailable, get_llm
from .schema import build_schema_context
from .skills import match_skill


@dataclass
class Answer:
    question: str
    sql: str
    result: QueryResult
    source: str            # 'skill:<name>' | 'llm' | 'error'
    message: str = ""


class Copilot:
    def __init__(self, db_path: str, llm=None):
        self.wh = Warehouse(db_path)
        self.llm = llm if llm is not None else get_llm()
        self._schema = None

    def schema_context(self) -> str:
        if self._schema is None:
            self._schema = build_schema_context(self.wh)
        return self._schema

    def ask(self, question: str) -> Answer:
        skill = match_skill(question)
        if skill is not None:
            sql, source = skill.sql, f"skill:{skill.name}"
        else:
            try:
                sql = self.llm.generate_sql(question, self.schema_context())
                source = "llm"
            except LLMUnavailable as exc:
                return Answer(question, "", None, "error", str(exc))

        try:
            result = self.wh.run(sql)
        except UnsafeQueryError as exc:
            return Answer(question, sql, None, "error", f"Blocked unsafe query: {exc}")
        except Exception as exc:  # noqa: BLE001 - surface any execution error cleanly
            return Answer(question, sql, None, "error", f"Query failed: {exc}")

        return Answer(question, result.sql, result, source)
