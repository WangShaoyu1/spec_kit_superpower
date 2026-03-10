import pytest


@pytest.fixture(autouse=True)
async def setup_db():
    """Override parent conftest's setup_db — unit tests don't need a database."""
    yield
