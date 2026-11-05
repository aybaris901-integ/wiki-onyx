import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.outbox import metadata


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    metadata.create_all(engine)
    return engine
