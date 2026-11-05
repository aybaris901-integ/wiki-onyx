"""Receives payment status events pushed by PayRail."""
import hashlib
import hmac

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from . import ach_guard
from .db import payments, payrail_events
from .status import apply_status

SIGNATURE_TOLERANCE_SECONDS = 300
STATUS_BY_EVENT = {"payment.succeeded": "succeeded", "payment.failed": "failed"}


class BadSignature(Exception):
    pass


def verify_signature(secret: str, timestamp: str, body: bytes, signature: str, now: int) -> None:
    """PayRail signs "<timestamp>.<body>" with HMAC-SHA256. The timestamp check stops replays."""
    try:
        age = abs(now - int(timestamp))
    except ValueError as exc:
        raise BadSignature("bad timestamp") from exc
    if age > SIGNATURE_TOLERANCE_SECONDS:
        raise BadSignature("timestamp outside tolerance")
    expected = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise BadSignature("signature mismatch")


def handle_event(engine, event: dict, now: int) -> dict | None:
    """Apply one PayRail event. Returns an event for the merchant if the status changed."""
    status = STATUS_BY_EVENT.get(event["type"])
    if status is None:
        return None
    try:
        with engine.begin() as conn:
            conn.execute(insert(payrail_events).values(id=event["id"], received_at=now))
            if _is_stale_card_failure(conn, event, status):
                return None
            if ach_guard.should_hold(conn, event["payment_id"], status, now):
                ach_guard.hold(conn, event["payment_id"], now)
                return None
            return apply_status(conn, event["payment_id"], status, now)
    except IntegrityError:
        return None  # already processed this event id


def _is_stale_card_failure(conn, event: dict, status: str) -> bool:
    """A card can't fail after succeeding (refunds and chargebacks are separate events), so this
    is an earlier attempt's failure arriving late. Only ACH can really fail after success."""
    if status != "failed":
        return False
    row = conn.execute(select(payments).where(payments.c.id == event["payment_id"])).mappings().first()
    return row is not None and row["method"] == "card" and row["status"] == "succeeded"
