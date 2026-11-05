from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.outbox import MAX_AGE_SECONDS, RETRY_DELAY_SECONDS, drain, enqueue, outbox

REQUEST = {"payment_id": "pay_1", "to": "ap@customer.example", "invoice_id": "inv_1", "amount_cents": 12500, "currency": "USD"}
PAYLOAD = {k: v for k, v in REQUEST.items() if k != "payment_id"}


def status(engine):
    with engine.connect() as conn:
        return conn.execute(select(outbox.c.status)).scalar_one()


def smtp_down(_message):
    raise OSError("connection refused")


def test_route_queues_without_sending(engine):
    response = TestClient(create_app(engine)).post("/internal/receipts", json=REQUEST)
    assert response.status_code == 202
    assert status(engine) == "queued"


def test_worker_sends_the_receipt(engine):
    enqueue(engine, "pay_1", PAYLOAD, now=100)
    sent = []
    assert drain(engine, sent.append, now=100) == 1
    assert "125.00 USD" in sent[0].get_content()
    assert status(engine) == "sent"


def test_same_payment_gets_one_receipt(engine):
    assert enqueue(engine, "pay_1", PAYLOAD, now=100) is True
    assert enqueue(engine, "pay_1", PAYLOAD, now=101) is False


def test_outage_delays_the_receipt_instead_of_losing_it(engine):
    enqueue(engine, "pay_1", PAYLOAD, now=100)
    assert drain(engine, smtp_down, now=100) == 0
    assert status(engine) == "queued"

    sent = []
    assert drain(engine, sent.append, now=101) == 0  # not due yet
    assert drain(engine, sent.append, now=100 + RETRY_DELAY_SECONDS) == 1


def test_gives_up_after_three_days(engine):
    enqueue(engine, "pay_1", PAYLOAD, now=100)
    drain(engine, smtp_down, now=100 + MAX_AGE_SECONDS)
    assert status(engine) == "dead"
