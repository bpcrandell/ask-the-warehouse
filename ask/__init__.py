"""ask-the-warehouse: a natural-language SQL copilot over a DuckDB warehouse.

Layers:
    db       - read-only DuckDB access with a query guardrail
    schema   - turns the live schema into grounding context for the model
    skills   - a reusable framework of curated, consistently-defined metrics
    llm      - pluggable model backend (Anthropic, or an offline stub)
    copilot  - orchestrates skill-match -> LLM -> validate -> execute
"""
__version__ = "0.1.0"
