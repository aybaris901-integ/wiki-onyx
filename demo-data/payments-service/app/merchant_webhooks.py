"""Tells merchants' systems when a payment changes status.

Deliveries are queued in Postgres and retried with exponential backoff and full jitter. The jitter
matters as much as the backoff: without it, every delivery that failed during a merchant's outage
comes back at the same moment and knocks them over again.
"""
import json
import random

import httpx
from sqlalchemy import insert, select, update

from .db import merchant_endpoints, webhook_deliveries

BASE_DELAY_SECONDS = 60
MAX_DELAY_SECONDS = 6 * 60 * 60
MAX_ATTEMPTS = 10  # worst case about 8.5 hours between first and last attempt
RETRYABLE_STATUS = {408, 429}


def next_delay(attempt: int, rng=random.random, retry_after: int | None = None) -> int:
    """Seconds to wait after failed attempt number `attempt`, counting from 1."""
    ceiling = min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * 2 ** (attempt - 1))
    delay = int(rng() * ceiling)
    if retry_after is not None:
        delay = max(delay, min(retry_after, MAX_DELAY_SECONDS))
    return delay


def notify(engine, event: dict, now: int) -> bool:
    """Queue a delivery. Never calls the merchant directly, so their outage can't block us."""
    with engine.begin() as conn:
        endpoint = conn.execute(
            select(merchant_endpoints).where(merchant_endpoints.c.merchant_id == event["merchant_id"])
        ).mappings().first()
        if endpoint is None:
            return False
        conn.execute(
            insert(webhook_deliveries).values(
                merchant_id=event["merchant_id"],
                url=endpoint["url"],
                payload=json.dumps(event),
                attempts=0,
                next_attempt_at=now,
                status="queued",
            )
        )
    return True


def process_due(engine, now: int, post=httpx.post, rng=random.random, limit: int = 100) -> int:
    """Attempt queued deliveries that are due. Returns how many were delivered."""
    with engine.connect() as conn:
        due = conn.execute(
            select(webhook_deliveries)
            .where(webhook_deliveries.c.status == "queued", webhook_deliveries.c.next_attempt_at <= now)
            .order_by(webhook_deliveries.c.next_attempt_at)
            .limit(limit)
        ).mappings().all()

    delivered = 0
    for delivery in due:
        values = _attempt(delivery, now, post, rng)
        delivered += values["status"] == "delivered"
        with engine.begin() as conn:
            conn.execute(update(webhook_deliveries).where(webhook_deliveries.c.id == delivery["id"]).values(**values))
    return delivered


def _attempt(delivery, now: int, post, rng) -> dict:
    attempts = delivery["attempts"] + 1
    retry_after = None
    try:
        response = post(delivery["url"], content=delivery["payload"], timeout=5.0)
        if response.status_code < 300:
            return {"attempts": attempts, "status": "delivered"}
        # Any other 4xx means the merchant's endpoint rejects this payload; retrying won't help.
        if response.status_code < 500 and response.status_code not in RETRYABLE_STATUS:
            return {"attempts": attempts, "status": "dead"}
        retry_after = _parse_retry_after(response.headers.get("retry-after"))
    except httpx.HTTPError:
        pass

    if attempts >= MAX_ATTEMPTS:
        return {"attempts": attempts, "status": "dead"}
    return {
        "attempts": attempts,
        "status": "queued",
        "next_attempt_at": now + next_delay(attempts, rng, retry_after),
    }


def _parse_retry_after(value: str | None) -> int | None:
    return int(value) if value and value.isdigit() else None
