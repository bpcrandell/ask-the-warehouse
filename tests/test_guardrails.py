import duckdb
import pytest

from ask.db import UnsafeQueryError, Warehouse


@pytest.mark.parametrize("bad_sql", [
    "drop table fct_funnel",
    "insert into fct_funnel values (1)",
    "update dim_dealers set status = 'x'",
    "delete from fct_funnel",
    "select 1; drop table fct_funnel",          # multi-statement
    "attach 'evil.db' as e",
    "pragma database_list",
    "copy fct_funnel to 'out.csv'",
    "",                                          # empty
])
def test_blocks_unsafe(bad_sql):
    with pytest.raises(UnsafeQueryError):
        Warehouse.check_safe(bad_sql)


@pytest.mark.parametrize("good_sql", [
    "select count(*) from fct_funnel",
    "with x as (select 1 as a) select a from x",
    "SELECT dealer_id FROM dim_dealers WHERE region = 'West'",
])
def test_allows_reads(good_sql):
    Warehouse.check_safe(good_sql)  # should not raise


def test_readonly_connection_rejects_writes(db_path):
    # Defense in depth: the connection itself is read-only.
    con = duckdb.connect(db_path, read_only=True)
    try:
        with pytest.raises(Exception):
            con.execute("create table hack (x int)")
    finally:
        con.close()


def test_run_enforces_limit(db_path):
    wh = Warehouse(db_path)
    result = wh.run("select * from fct_funnel")
    assert "limit" in result.sql.lower()
    assert len(result.rows) <= 200
