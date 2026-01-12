"""Asks PayRail for the status of every open payment. Runs every 30 seconds."""
from sqlalchemy import select

from .db import payments
from .merchant_webhooks import notify
from .status import apply_status


def poll_open_payments(engine, gateway, now: int) -> int:
    with engine.connect() as conn:
        open_ids = conn.execute(select(payments.c.id).where(payments.c.status == "pending")).scalars().all()

    changed = 0
    for payment_id in open_ids:
        status = gateway.get_payment(payment_id).status
        with engine.begin() as conn:
            event = apply_status(conn, payment_id, status, now)
        if event:
            notify(engine, event)
            changed += 1
    return changed
