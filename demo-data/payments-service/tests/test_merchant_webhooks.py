import httpx
from sqlalchemy import insert, select

from app.db import merchant_endpoints, webhook_deliveries
from app.merchant_webhooks import BASE_DELAY_SECONDS, MAX_ATTEMPTS, next_delay, notify, process_due

EVENT = {"merchant_id": "m_1", "invoice_id": "inv_1", "payment_id": "pay_1", "status": "succeeded"}


def queue_one(engine):
    with engine.begin() as conn:
        conn.execute(insert(merchant_endpoints).values(merchant_id="m_1", url="https://erp.customer.example/hook"))
    assert notify(engine, EVENT, now=1000)


def delivery(engine):
    with engine.connect() as conn:
        return conn.execute(select(webhook_deliveries)).mappings().one()


def answering(status, headers=None):
    return lambda url, content, timeout: httpx.Response(status, headers=headers)


def test_delay_doubles_and_is_jittered():
    assert next_delay(1, rng=lambda: 1.0) == BASE_DELAY_SECONDS
    assert next_delay(4, rng=lambda: 1.0) == BASE_DELAY_SECONDS * 8
    assert next_delay(4, rng=lambda: 0.5) == BASE_DELAY_SECONDS * 4


def test_retry_after_sets_a_floor():
    assert next_delay(1, rng=lambda: 0.0, retry_after=120) == 120


def test_no_endpoint_means_nothing_queued(engine):
    assert notify(engine, EVENT, now=1000) is False


def test_success_is_delivered(engine):
    queue_one(engine)
    assert process_due(engine, now=1000, post=answering(200)) == 1
    assert delivery(engine)["status"] == "delivered"


def test_server_error_schedules_retry(engine):
    queue_one(engine)
    process_due(engine, now=1000, post=answering(503), rng=lambda: 1.0)
    row = delivery(engine)
    assert row["status"] == "queued" and row["attempts"] == 1
    assert row["next_attempt_at"] == 1000 + BASE_DELAY_SECONDS


def test_not_retried_before_it_is_due(engine):
    queue_one(engine)
    process_due(engine, now=1000, post=answering(503), rng=lambda: 1.0)
    process_due(engine, now=1001, post=answering(200))
    assert delivery(engine)["status"] == "queued"


def test_rejected_payload_is_not_retried(engine):
    queue_one(engine)
    process_due(engine, now=1000, post=answering(400))
    assert delivery(engine)["status"] == "dead"


def test_rate_limit_is_retried_after_the_merchants_delay(engine):
    queue_one(engine)
    process_due(engine, now=1000, post=answering(429, {"retry-after": "300"}), rng=lambda: 0.0)
    row = delivery(engine)
    assert row["status"] == "queued" and row["next_attempt_at"] == 1300


def test_gives_up_after_max_attempts(engine):
    queue_one(engine)

    def fail(url, content, timeout):
        raise httpx.ConnectError("down")

    now = 1000
    for _ in range(MAX_ATTEMPTS):
        process_due(engine, now=now, post=fail, rng=lambda: 0.0)
    assert delivery(engine)["status"] == "dead"
    assert delivery(engine)["attempts"] == MAX_ATTEMPTS
