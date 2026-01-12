"""Server-side sessions, looked up on every dashboard and reporting request."""
import secrets

from sqlalchemy import BigInteger, Column, MetaData, String, Table, delete, insert, select

SESSION_TTL_SECONDS = 8 * 60 * 60

metadata = MetaData()
sessions = Table(
    "sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("expires_at", BigInteger, nullable=False),
)


class PostgresSessionStore:
    def __init__(self, engine):
        self._engine = engine

    def create(self, user_id: str, now: int) -> str:
        session_id = secrets.token_urlsafe(24)
        with self._engine.begin() as conn:
            conn.execute(insert(sessions).values(id=session_id, user_id=user_id, expires_at=now + SESSION_TTL_SECONDS))
        return session_id

    def get_user_id(self, session_id: str, now: int) -> str | None:
        with self._engine.connect() as conn:
            row = conn.execute(select(sessions).where(sessions.c.id == session_id)).mappings().first()
        if row is None or row["expires_at"] <= now:
            return None
        return row["user_id"]

    def delete(self, session_id: str) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(sessions).where(sessions.c.id == session_id))
