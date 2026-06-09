import pytest

from ask.demo_data import build


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    """A freshly built demo warehouse in a temp dir, shared across the test session."""
    path = str(tmp_path_factory.mktemp("warehouse") / "warehouse.duckdb")
    build(path)
    return path
