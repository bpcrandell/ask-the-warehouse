"""Turn the live warehouse schema into grounding context for the model.

Only real table and column names are exposed, plus short business descriptions
and the canonical metric definitions, so the model writes SQL against what
actually exists instead of guessing.
"""
from __future__ import annotations

from .db import Warehouse

TABLE_DOCS = {
    "dim_dealers": "One row per dealer (the dealer master): group, region, state, fulfillment carrier, status.",
    "fct_funnel": ("One row per lead. is_quoted = a quote was generated; is_bound = it converted to a policy. "
                   "quote_monthly_premium / policy_monthly_premium are dollars per month."),
    "mart_dealer_performance": ("Dealer x month rollup. Metric definitions: "
                                "lead_to_quote_rate = quotes/leads; quote_to_policy_rate = policies/quotes; "
                                "lead_to_policy_rate = policies/leads; "
                                "bound_premium_value = sum(monthly_premium * term_months) for bound policies."),
}


def build_schema_context(wh: Warehouse) -> str:
    lines = [
        "Schema for a DuckDB warehouse covering an embedded auto-insurance dealer channel.",
        "The funnel runs: calls -> leads -> quotes -> policies.",
        "",
        "Tables:",
    ]
    for table in wh.list_tables():
        doc = TABLE_DOCS.get(table, "")
        cols = ", ".join(f"{name} {dtype}" for name, dtype in wh.columns(table))
        lines.append(f"- {table}: {doc}")
        lines.append(f"    columns: {cols}")
    return "\n".join(lines)
