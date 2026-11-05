"""Server-side sessions, looked up on every dashboard and reporting request.

Sessions live in Redis rather than Postgres because this lookup runs on almost every page load and was
the slowest part of request handling. Losing Redis logs people out; it never loses money or
customer data. Do not copy this choice for anything that has to survive a failover.

Each session also holds the hash of its current refresh token. Refresh tokens rotate on every
use, so seeing an old one means two parties hold the token, one of whom may be an attacker. We
can't tell which, so we end the session.
"""
import hashlib
import hmac
import json
import secrets

SESSION_TTL_SECONDS = 8 * 60 * 60
KEY_PREFIX = "session:"


class RefreshRejected(Exception):
    pass


def _hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


class RedisSessionStore:
    def __init__(self, redis_client):
        self._redis = redis_client

    def create(self, user_id: str) -> tuple[str, str]:
        """Returns (session id, refresh token)."""
        session_id = secrets.token_urlsafe(24)
        secret = secrets.token_urlsafe(32)
        self._save(session_id, user_id, secret)
        return session_id, f"{session_id}.{secret}"

    def get_user_id(self, session_id: str) -> str | None:
        session = self._load(session_id)
        return session["user_id"] if session else None

    def rotate_refresh_token(self, refresh_token: str) -> tuple[str, str, str]:
        """Returns (session id, user id, new refresh token)."""
        session_id, _, secret = refresh_token.partition(".")
        session = self._load(session_id)
        if session is None:
            raise RefreshRejected("session ended")
        if not hmac.compare_digest(session["refresh_hash"], _hash(secret)):
            self.delete(session_id)  # an old token came back: treat the session as stolen
            raise RefreshRejected("refresh token reused")
        new_secret = secrets.token_urlsafe(32)
        self._save(session_id, session["user_id"], new_secret)
        return session_id, session["user_id"], f"{session_id}.{new_secret}"

    def delete(self, session_id: str) -> None:
        self._redis.delete(KEY_PREFIX + session_id)

    def _save(self, session_id: str, user_id: str, secret: str) -> None:
        value = json.dumps({"user_id": user_id, "refresh_hash": _hash(secret)})
        self._redis.set(KEY_PREFIX + session_id, value, ex=SESSION_TTL_SECONDS)

    def _load(self, session_id: str) -> dict | None:
        value = self._redis.get(KEY_PREFIX + session_id)
        return json.loads(value) if value is not None else None
