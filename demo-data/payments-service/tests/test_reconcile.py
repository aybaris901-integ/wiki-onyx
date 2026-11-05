from sqlalchemy import select

from app.charges import pay_invoice
from app.db import payments
from app.reconcile import STUCK_AFTER_SECONDS, reconcile_stuck_payments


def test_leaves_recent_payments_alone(engine, gateway):
    pay_invoice(engine, gateway, "inv_1", "card", now=100)
    assert reconcile_stuck_payments(engine, gateway, now=100 + STUCK_AFTER_SECONDS - 1) == 0


def test_picks_up_payment_whose_webhook_never_came(engine, gateway):
    payment = pay_invoice(engine, gateway, "inv_1", "card", now=100)
    gateway.statuses[payment["payment_id"]] = "succeeded"
    assert reconcile_stuck_payments(engine, gateway, now=100 + STUCK_AFTER_SECONDS) == 1
    with engine.connect() as conn:
        assert conn.execute(select(payments.c.status)).scalar_one() == "succeeded"
