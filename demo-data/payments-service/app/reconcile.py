"""Safety net for webhooks that never arrived. Runs hourly.

Polling every open payment every 30 seconds is what we moved away from. This only asks about
payments that have been pending for over an hour, which is normally a handful.
"""
from sqlalchemy import select

from .db import payments
from .merchant_webhooks import notify
from .status import apply_status

STUCK_AFTER_SECONDS = 60 * 60


def reconcile_stuck_payments(engine, gateway, now: int) -> int:
    with engine.connect() as conn:
        stuck_ids = conn.execute(
            select(payments.c.id).where(
                payments.c.status == "pending", payments.c.updated_at <= now - STUCK_AFTER_SECONDS
            )
        ).scalars().all()

    changed = 0
    for payment_id in stuck_ids:
        status = gateway.get_payment(payment_id).status
        with engine.begin() as conn:
            event = apply_status(conn, payment_id, status, now)
        if event:
            notify(engine, event)
            changed += 1
    return changed
