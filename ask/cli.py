"""Command-line entry point:  python -m ask "your question" """
from __future__ import annotations

import argparse
import os

from .copilot import Copilot
from .demo_data import DEFAULT_DB


def _print_table(columns, rows, max_rows=25):
    if not rows:
        print("(no rows)")
        return
    widths = [len(str(c)) for c in columns]
    shown = rows[:max_rows]
    for row in shown:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    header = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(columns))
    print(header)
    print("-" * len(header))
    for row in shown:
        print(" | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)))
    if len(rows) > max_rows:
        print(f"... ({len(rows)} rows total)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ask", description="Ask the warehouse a question in plain English.")
    parser.add_argument("question", nargs="+", help="your question, in words")
    parser.add_argument("--db", default=DEFAULT_DB, help="path to the DuckDB warehouse")
    parser.add_argument("--sql-only", action="store_true",
                        help="print the generated SQL without running it")
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print(f"Note: warehouse not found at {args.db}. Run: python scripts/build_demo_db.py")
        return 1

    answer = Copilot(args.db).ask(" ".join(args.question))

    if answer.source == "error":
        print(f"Note: {answer.message}")
        if answer.sql:
            print(f"\nSQL:\n{answer.sql}")
        return 1

    print(f"Q: {answer.question}")
    print(f"[answered via {answer.source}]\n")
    print(answer.sql.strip() + "\n")
    if not args.sql_only:
        _print_table(answer.result.columns, answer.result.rows)
    return 0
