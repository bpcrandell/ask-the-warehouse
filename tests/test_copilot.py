from ask.copilot import Copilot
from ask.llm import StubLLM
from ask.skills import match_skill


def test_overall_funnel_skill_answers_offline(db_path):
    cop = Copilot(db_path, llm=StubLLM())
    ans = cop.ask("what is the overall conversion rate?")
    assert ans.source == "skill:overall_funnel"
    assert ans.result is not None and ans.result.rows
    assert "leads" in [c.lower() for c in ans.result.columns]


def test_top_dealers_skill(db_path):
    cop = Copilot(db_path, llm=StubLLM())
    ans = cop.ask("who are the top performing dealers?")
    assert ans.source == "skill:top_dealers"
    assert ans.result.rows


def test_open_question_without_llm_is_graceful(db_path):
    cop = Copilot(db_path, llm=StubLLM())
    ans = cop.ask("list every dealer name in alphabetical order")
    assert ans.source == "error"
    assert "ANTHROPIC_API_KEY" in ans.message


def test_skill_matching_is_keyword_based():
    assert match_skill("show me conversion by source").name == "conversion_by_source"
    assert match_skill("break it down by region").name == "by_region"
    assert match_skill("what's the weather") is None
