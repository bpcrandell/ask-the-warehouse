"""A reusable framework of curated, consistently-defined metrics.

Each Skill pins the exact SQL for a common business question, so a metric like
"conversion rate" is always computed the same way no matter how it's asked.
The copilot checks skills first; anything not covered falls through to the LLM.
This is the pattern that keeps business logic consistent instead of every
answer re-deriving a definition.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Skill:
    name: str
    description: str
    keywords: list
    sql: str

    def matches(self, question: str) -> bool:
        q = question.lower()
        return any(k in q for k in self.keywords)


SKILLS = [
    Skill(
        name="overall_funnel",
        description="Overall lead -> quote -> policy funnel and conversion rate.",
        keywords=["overall", "funnel", "conversion rate", "total leads",
                  "how many leads", "how many policies", "how many quotes"],
        sql="""
            select
                count(*) as leads,
                sum(case when is_quoted then 1 else 0 end) as quotes,
                sum(case when is_bound then 1 else 0 end) as policies,
                round(sum(case when is_bound then 1 else 0 end) * 1.0 / count(*), 3)
                    as lead_to_policy_rate
            from fct_funnel
        """,
    ),
    Skill(
        name="conversion_by_source",
        description="Conversion broken down by lead source / channel.",
        keywords=["by source", "by channel", "lead source", "which channel",
                  "call center", "qr code"],
        sql="""
            select
                lead_source,
                count(*) as leads,
                sum(case when is_bound then 1 else 0 end) as policies,
                round(sum(case when is_bound then 1 else 0 end) * 1.0 / count(*), 3)
                    as lead_to_policy_rate
            from fct_funnel
            group by 1
            order by leads desc
        """,
    ),
    Skill(
        name="top_dealers",
        description="Top dealers by lead-to-policy conversion (minimum 30 leads).",
        keywords=["top dealer", "best dealer", "best performing", "top performing",
                  "highest conversion", "which dealers"],
        sql="""
            select
                d.dealer_name,
                d.region,
                sum(m.leads) as leads,
                sum(m.policies) as policies,
                round(sum(m.policies) * 1.0 / sum(m.leads), 3) as lead_to_policy_rate
            from mart_dealer_performance m
            join dim_dealers d on m.dealer_id = d.dealer_id
            group by 1, 2
            having sum(m.leads) >= 30
            order by lead_to_policy_rate desc
            limit 10
        """,
    ),
    Skill(
        name="by_region",
        description="Funnel performance by region.",
        keywords=["by region", "which region", "per region", "across regions"],
        sql="""
            select
                d.region,
                count(*) as leads,
                sum(case when f.is_bound then 1 else 0 end) as policies,
                round(sum(case when f.is_bound then 1 else 0 end) * 1.0 / count(*), 3)
                    as lead_to_policy_rate
            from fct_funnel f
            join dim_dealers d on f.dealer_id = d.dealer_id
            group by 1
            order by lead_to_policy_rate desc
        """,
    ),
    Skill(
        name="bound_premium",
        description="Total bound premium value (annualized).",
        keywords=["premium", "revenue", "bound value", "total value", "how much premium"],
        sql="select round(sum(bound_premium_value), 2) as total_bound_premium_value "
            "from mart_dealer_performance",
    ),
]


def match_skill(question: str):
    """Return the first skill whose keywords appear in the question, else None."""
    for skill in SKILLS:
        if skill.matches(question):
            return skill
    return None
