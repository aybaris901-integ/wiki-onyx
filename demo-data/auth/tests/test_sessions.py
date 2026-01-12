from sqlalchemy import create_engine

from app.sessions import SESSION_TTL_SECONDS, PostgresSessionStore, metadata


def store():
    engine = create_engine("sqlite+pysqlite://")
    metadata.create_all(engine)
    return PostgresSessionStore(engine)


def test_create_get_delete():
    sessions = store()
    session_id = sessions.create("u_1", now=100)
    assert sessions.get_user_id(session_id, now=101) == "u_1"
    sessions.delete(session_id)
    assert sessions.get_user_id(session_id, now=102) is None


def test_expires():
    sessions = store()
    session_id = sessions.create("u_1", now=100)
    assert sessions.get_user_id(session_id, now=100 + SESSION_TTL_SECONDS) is None
