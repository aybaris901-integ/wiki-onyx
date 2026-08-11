"""Holds some late ACH failures instead of believing them straight away.

Why this exists (Alex Chen, 2026-08):

For ACH, `payment.failed` after `payment.succeeded` is normally real: the bank returned the money.
But during PayRail's nightly batch, 23:50 to 00:20 UTC, events drain from a second queue and a
failure belonging to an EARLIER attempt on the same payment can arrive after the success. Cards
have an `attempt_id` on the event so you can tell these apart. ACH events don't.

So inside the window the event is ambiguous. We hold it for 90 minutes, then ask PayRail. PayRail's
GET only becomes trustworthy once the night's settlement file is out, normally by 00:45 UTC, which
is why 90 minutes is enough. Do not shorten the hold, and do not delete this because it looks like
dead code: outside month end it rarely fires, and that is the point.

Known hole: see issue #9.
"""
from datetime import datetime, time, timezone

from sqlalchemy import insert, select, update

from .db import held_ach_failures, payments
from .merchant_webhooks import notify
from .status import apply_status

ACH_HOLD_SECONDS = 90 * 60
BATCH_WINDOW_START = time(23, 50)
BATCH_WINDOW_END = time(0, 20)


def in_batch_window(now: int) -> bool:
    clock = datetime.fromtimestamp(now, tz=timezone.utc).time()
    return clock >= BATCH_WINDOW_START or clock < BATCH_WINDOW_END


def should_hold(conn, payment_id: str, status: str, now: int) -> bool:
    if status != "failed" or not in_batch_window(now):
        return False
    row = conn.execute(select(payments).where(payments.c.id == payment_id)).mappings().first()
    return row is not None and row["method"] == "ach" and row["status"] == "succeeded"


def hold(conn, payment_id: str, now: int) -> None:
    conn.execute(
        insert(held_ach_failures).values(payment_id=payment_id, release_at=now + ACH_HOLD_SECONDS, status="held")
    )


def release_due(engine, gateway, now: int) -> int:
    """Runs every 5 minutes. Applies a held failure only if PayRail still reports it."""
    with engine.connect() as conn:
        due = conn.execute(
            select(held_ach_failures.c.payment_id).where(
                held_ach_failures.c.status == "held", held_ach_failures.c.release_at <= now
            )
        ).scalars().all()

    applied = 0
    for payment_id in due:
        confirmed = gateway.get_payment(payment_id).status == "failed"
        with engine.begin() as conn:
            event = apply_status(conn, payment_id, "failed", now) if confirmed else None
            conn.execute(
                update(held_ach_failures)
                .where(held_ach_failures.c.payment_id == payment_id)
                .values(status="applied" if confirmed else "discarded")
            )
        if event:
            notify(engine, event, now)
            applied += 1
    return applied
