"""Server-side sessions, looked up on every dashboard and reporting request.

Sessions live in Redis rather than Postgres because this lookup runs on almost every page load and was
the slowest part of request handling. Losing Redis logs people out; it never loses money or
customer data. Do not copy this choice for anything that has to survive a failover.
"""
import secrets

SESSION_TTL_SECONDS = 8 * 60 * 60
KEY_PREFIX = "session:"


class RedisSessionStore:
    def __init__(self, redis_client):
        self._redis = redis_client

    def create(self, user_id: str) -> str:
        session_id = secrets.token_urlsafe(24)
        self._redis.set(KEY_PREFIX + session_id, user_id, ex=SESSION_TTL_SECONDS)
        return session_id

    def get_user_id(self, session_id: str) -> str | None:
        value = self._redis.get(KEY_PREFIX + session_id)
        return value.decode() if value is not None else None

    def delete(self, session_id: str) -> None:
        self._redis.delete(KEY_PREFIX + session_id)
