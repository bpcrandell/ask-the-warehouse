"""Build a small, self-contained synthetic warehouse for the copilot to query.

Three tables mimic the marts of a dealer-channel insurance warehouse. All data
is synthetic, reproducible (fixed seed), and contains no real information.
"""
import os
import random
from datetime import date, timedelta

import duckdb

DEFAULT_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "warehouse.duckdb"
)

_GROUPS = ["Great Lakes Auto Group", "Sunbelt Motors", "Pacific Crest Dealers",
           "Heartland Automotive", "Independent"]
_REGIONS = {"Midwest": ["MI", "OH", "IL"], "South": ["TX", "FL", "GA"],
            "West": ["CA", "WA", "AZ"], "Northeast": ["NY", "PA", "NJ"]}
_CARRIERS = ["Carrier A", "Carrier B", "In-House Agency"]
_BRANDS = ["Ford", "Chevrolet", "Toyota", "Honda", "Kia", "Subaru", "Jeep", "GMC"]
_CITIES = ["Detroit", "Austin", "Sacramento", "Cleveland", "Tampa", "Denver",
           "Albany", "Charlotte", "Phoenix", "Seattle", "Dallas", "Atlanta"]
_SOURCES = ["Call Center", "Web", "QR Code"]
_DEPARTMENTS = ["Sales", "Service", "F&I"]


def build(db_path: str = DEFAULT_DB, seed: int = 42) -> dict:
    """Generate the warehouse at db_path. Returns a dict of table -> row count."""
    random.seed(seed)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    dealers = []
    for i in range(1, 41):
        region = random.choice(list(_REGIONS))
        dealers.append((
            i, f"{random.choice(_CITIES)} {random.choice(_BRANDS)}",
            random.choice(_GROUPS), region, random.choice(_REGIONS[region]),
            random.choice(_CARRIERS),
            random.choices(["active", "paused", "churned"], weights=[80, 12, 8])[0],
        ))

    funnel = []
    lead_id = 0
    start = date(2025, 1, 1)
    for _ in range(4000):
        d = random.choice(dealers)
        lead_id += 1
        lead_date = start + timedelta(days=random.randint(0, 350))
        is_quoted = random.random() < 0.55
        quote_premium = round(random.uniform(95, 310), 2) if is_quoted else None
        is_bound = is_quoted and random.random() < 0.40
        policy_premium = quote_premium if is_bound else None
        term = random.choice([6, 12]) if is_bound else None
        funnel.append((lead_id, d[0], random.choice(_SOURCES),
                       random.choices(_DEPARTMENTS, weights=[60, 25, 15])[0],
                       lead_date, quote_premium, policy_premium, term, is_quoted, is_bound))

    if os.path.exists(db_path):
        os.remove(db_path)
    con = duckdb.connect(db_path)
    try:
        con.execute("""create table dim_dealers (
            dealer_id integer, dealer_name varchar, dealer_group varchar,
            region varchar, state varchar, fulfillment_carrier varchar, status varchar)""")
        con.executemany("insert into dim_dealers values (?,?,?,?,?,?,?)", dealers)

        con.execute("""create table fct_funnel (
            lead_id integer, dealer_id integer, lead_source varchar, department varchar,
            lead_date date, quote_monthly_premium decimal(10,2),
            policy_monthly_premium decimal(10,2), term_months integer,
            is_quoted boolean, is_bound boolean)""")
        con.executemany("insert into fct_funnel values (?,?,?,?,?,?,?,?,?,?)", funnel)

        con.execute("""create table mart_dealer_performance as
            select f.dealer_id, d.dealer_name, d.dealer_group, d.region, d.state,
                   strftime(f.lead_date, '%Y-%m') as year_month,
                   count(*) as leads,
                   sum(case when f.is_quoted then 1 else 0 end) as quotes,
                   sum(case when f.is_bound then 1 else 0 end) as policies,
                   round(sum(case when f.is_quoted then 1 else 0 end)*1.0/count(*),3) as lead_to_quote_rate,
                   round(sum(case when f.is_bound then 1 else 0 end)*1.0
                         / nullif(sum(case when f.is_quoted then 1 else 0 end),0),3) as quote_to_policy_rate,
                   round(sum(case when f.is_bound then 1 else 0 end)*1.0/count(*),3) as lead_to_policy_rate,
                   sum(case when f.is_bound then f.policy_monthly_premium*f.term_months else 0 end) as bound_premium_value
            from fct_funnel f join dim_dealers d on f.dealer_id=d.dealer_id
            group by 1,2,3,4,5,6""")

        counts = {t: con.execute(f"select count(*) from {t}").fetchone()[0]
                  for t in ["dim_dealers", "fct_funnel", "mart_dealer_performance"]}
    finally:
        con.close()
    return counts
