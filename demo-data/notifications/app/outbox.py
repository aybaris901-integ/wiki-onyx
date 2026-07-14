"""Durable queue for receipts, stored in a Postgres table.

The API writes a row and returns; a worker does the sending. A provider outage now delays receipts
instead of losing them. Delivery is at least once: if the worker dies between sending and marking
the row, the customer gets a second receipt. A duplicate receipt is harmless, a missing one sends
an accounts team to our support inbox.
"""
import json

from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, Text, insert, select, update
from sqlalchemy.exc import IntegrityError

from .mailer import build_receipt

RETRY_DELAY_SECONDS = 5 * 60
MAX_AGE_SECONDS = 72 * 60 * 60  # after this a receipt goes to "dead" and support resends by hand

metadata = MetaData()
outbox = Table(
    "receipt_outbox",
    metadata,
    Column("payment_id", String, primary_key=True),  # one receipt per payment, even if asked twice
    Column("payload", Text, nullable=False),
    Column("status", String, nullable=False),  # queued | sent | dead
    Column("attempts", Integer, nullable=False),
    Column("created_at", BigInteger, nullable=False),
    Column("next_attempt_at", BigInteger, nullable=False),
)


def enqueue(engine, payment_id: str, payload: dict, now: int) -> bool:
    try:
        with engine.begin() as conn:
            conn.execute(
                insert(outbox).values(
                    payment_id=payment_id,
                    payload=json.dumps(payload),
                    status="queued",
                    attempts=0,
                    created_at=now,
                    next_attempt_at=now,
                )
            )
        return True
    except IntegrityError:
        return False  # already queued for this payment


def drain(engine, send, now: int, limit: int = 100) -> int:
    """Send receipts that are due. Returns how many were sent."""
    with engine.connect() as conn:
        due = conn.execute(
            select(outbox)
            .where(outbox.c.status == "queued", outbox.c.next_attempt_at <= now)
            .order_by(outbox.c.created_at)
            .limit(limit)
        ).mappings().all()

    sent = 0
    for row in due:
        values = {"attempts": row["attempts"] + 1}
        try:
            send(build_receipt(**json.loads(row["payload"])))
            values["status"] = "sent"
            sent += 1
        except OSError:
            if now - row["created_at"] >= MAX_AGE_SECONDS:
                values["status"] = "dead"
            else:
                values["next_attempt_at"] = now + RETRY_DELAY_SECONDS
        with engine.begin() as conn:
            conn.execute(update(outbox).where(outbox.c.payment_id == row["payment_id"]).values(**values))
    return sent
