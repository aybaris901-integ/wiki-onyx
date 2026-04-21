"""Idempotency keys for charging.

A timeout from PayRail does not mean the charge failed. On 2026-04-14 (INC-2026-007) we retried
after timeouts and charged 37 invoices twice. Every charge now needs a key from the caller, and a
key can only ever produce one charge.

Keys live in Postgres, not Redis, on purpose: this record is what stands between a customer and a
duplicate charge, so it has to survive a Redis failover or eviction. See PR #4.
"""
import hashlib
import json

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from .db import idempotency_keys

RETENTION_SECONDS = 7 * 24 * 60 * 60


class KeyInProgress(Exception):
    """The first request with this key hasn't finished, or its outcome is unknown."""


class KeyReused(Exception):
    """The key was already used for a different request."""


def request_hash(*parts) -> str:
    return hashlib.sha256(":".join(str(part) for part in parts).encode()).hexdigest()


def claim(engine, merchant_id: str, key: str, hash_: str, now: int) -> tuple[int, dict] | None:
    """Returns None if we now own the key, or the stored (status, body) to replay."""
    try:
        with engine.begin() as conn:
            conn.execute(
                insert(idempotency_keys).values(
                    merchant_id=merchant_id, key=key, request_hash=hash_, status="in_progress", created_at=now
                )
            )
        return None
    except IntegrityError:
        pass  # the primary key is the lock: only one request can ever insert this key

    with engine.connect() as conn:
        row = conn.execute(
            select(idempotency_keys).where(
                idempotency_keys.c.merchant_id == merchant_id, idempotency_keys.c.key == key
            )
        ).mappings().one()
    if row["request_hash"] != hash_:
        raise KeyReused(key)
    if row["status"] == "in_progress":
        raise KeyInProgress(key)
    return row["response_code"], json.loads(row["response_body"])


def complete(engine, merchant_id: str, key: str, code: int, body: dict) -> None:
    with engine.begin() as conn:
        conn.execute(
            update(idempotency_keys)
            .where(idempotency_keys.c.merchant_id == merchant_id, idempotency_keys.c.key == key)
            .values(status="completed", response_code=code, response_body=json.dumps(body))
        )


def purge_expired(engine, now: int) -> int:
    with engine.begin() as conn:
        result = conn.execute(delete(idempotency_keys).where(idempotency_keys.c.created_at <= now - RETENTION_SECONDS))
    return result.rowcount
