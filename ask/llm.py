"""Pluggable model backend.

AnthropicLLM uses Claude to translate a question into read-only SQL, with the
schema pinned in a cached system prompt (so the grounding context is sent once
and reused across calls). StubLLM is the offline fallback: the curated skills
answer the common questions without any model, and open-ended questions ask the
user to set an API key. `get_llm` picks the right one based on the environment.
"""
from __future__ import annotations

import os
import re

SYSTEM_RULES = (
    "You translate a business question into a single read-only DuckDB SQL query.\n"
    "Rules:\n"
    "- Output ONLY one SQL statement inside a ```sql code block. No prose.\n"
    "- SELECT or WITH only. Never insert, update, delete, or change data.\n"
    "- Use only the tables and columns listed below; do not invent columns.\n"
    "- Prefer mart_dealer_performance for pre-computed metrics.\n"
    "- If the question cannot be answered from this schema, return: "
    "select 'unanswerable' as note.\n\n"
)


class LLMUnavailable(RuntimeError):
    """Raised when no live model is configured and a skill did not match."""


def _extract_sql(text: str) -> str:
    m = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


class AnthropicLLM:
    def __init__(self, model: str):
        import anthropic  # imported lazily so the package works without it
        self.client = anthropic.Anthropic()
        self.model = model

    def generate_sql(self, question: str, schema_context: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=700,
            system=[{
                "type": "text",
                "text": SYSTEM_RULES + schema_context,
                "cache_control": {"type": "ephemeral"},  # cache the grounding context
            }],
            messages=[{"role": "user", "content": question}],
        )
        text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
        return _extract_sql(text)


class StubLLM:
    """Offline fallback used when ANTHROPIC_API_KEY is not set."""

    def generate_sql(self, question: str, schema_context: str) -> str:
        raise LLMUnavailable(
            "No live model configured. Set ANTHROPIC_API_KEY to ask open-ended "
            "questions, or rephrase to one of the supported metrics (see the "
            "examples in the README)."
        )


def get_llm(model: str | None = None):
    model = model or os.environ.get("ASK_MODEL", "claude-sonnet-4-5")
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return AnthropicLLM(model)
        except Exception:
            return StubLLM()
    return StubLLM()
