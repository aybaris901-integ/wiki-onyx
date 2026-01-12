from sqlalchemy import select

from app.charges import pay_invoice
from app.db import payments
from app.polling import poll_open_payments


def test_poll_applies_new_status(engine, gateway, monkeypatch):
    sent = []
    monkeypatch.setattr("app.polling.notify", lambda engine, event: sent.append(event))
    payment = pay_invoice(engine, gateway, "inv_1", "card", now=100)
    gateway.statuses[payment["payment_id"]] = "succeeded"

    assert poll_open_payments(engine, gateway, now=130) == 1

    with engine.connect() as conn:
        assert conn.execute(select(payments.c.status)).scalar_one() == "succeeded"
    assert sent[0]["status"] == "succeeded"
