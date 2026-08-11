from datetime import datetime, timezone

from sqlalchemy import select

from app import ach_guard
from app.charges import pay_invoice
from app.db import held_ach_failures, invoices, payments
from app.payrail_webhooks import handle_event
from app.status import apply_status

NIGHT = int(datetime(2026, 8, 11, 23, 55, tzinfo=timezone.utc).timestamp())
JUST_AFTER_MIDNIGHT = int(datetime(2026, 8, 12, 0, 5, tzinfo=timezone.utc).timestamp())
MIDDAY = int(datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc).timestamp())


def succeeded_payment(engine, gateway, method):
    _, body = pay_invoice(engine, gateway, "inv_1", method, "m_1", "key", now=100)
    with engine.begin() as conn:
        apply_status(conn, body["payment_id"], "succeeded", now=101)
    return body["payment_id"]


def failed_event(payment_id, event_id="evt_failed"):
    return {"id": event_id, "type": "payment.failed", "payment_id": payment_id}


def status(engine):
    with engine.connect() as conn:
        return conn.execute(select(payments.c.status)).scalar_one()


def test_window_wraps_midnight():
    assert ach_guard.in_batch_window(NIGHT)
    assert ach_guard.in_batch_window(JUST_AFTER_MIDNIGHT)
    assert not ach_guard.in_batch_window(MIDDAY)


def test_ach_failure_outside_window_is_a_real_return(engine, gateway):
    payment_id = succeeded_payment(engine, gateway, "ach")
    assert handle_event(engine, failed_event(payment_id), now=MIDDAY)["status"] == "failed"
    assert status(engine) == "failed"


def test_ach_failure_inside_window_is_held(engine, gateway):
    payment_id = succeeded_payment(engine, gateway, "ach")
    assert handle_event(engine, failed_event(payment_id), now=NIGHT) is None
    assert status(engine) == "succeeded"


def test_stale_failure_is_discarded_if_payrail_says_succeeded(engine, gateway):
    payment_id = succeeded_payment(engine, gateway, "ach")
    handle_event(engine, failed_event(payment_id), now=NIGHT)
    gateway.statuses[payment_id] = "succeeded"

    assert ach_guard.release_due(engine, gateway, now=NIGHT + ach_guard.ACH_HOLD_SECONDS) == 0

    assert status(engine) == "succeeded"
    with engine.connect() as conn:
        assert conn.execute(select(held_ach_failures.c.status)).scalar_one() == "discarded"


def test_real_return_is_applied_when_payrail_confirms(engine, gateway):
    payment_id = succeeded_payment(engine, gateway, "ach")
    handle_event(engine, failed_event(payment_id), now=NIGHT)
    gateway.statuses[payment_id] = "failed"

    assert ach_guard.release_due(engine, gateway, now=NIGHT + ach_guard.ACH_HOLD_SECONDS) == 1

    assert status(engine) == "failed"
    with engine.connect() as conn:
        assert conn.execute(select(invoices.c.status)).scalar_one() == "open"


def test_not_released_early(engine, gateway):
    payment_id = succeeded_payment(engine, gateway, "ach")
    handle_event(engine, failed_event(payment_id), now=NIGHT)
    gateway.statuses[payment_id] = "failed"
    ach_guard.release_due(engine, gateway, now=NIGHT + ach_guard.ACH_HOLD_SECONDS - 1)
    assert status(engine) == "succeeded"


def test_late_card_failure_is_ignored_at_any_time(engine, gateway):
    payment_id = succeeded_payment(engine, gateway, "card")
    assert handle_event(engine, failed_event(payment_id), now=MIDDAY) is None
    assert status(engine) == "succeeded"


def test_first_failure_on_pending_ach_is_not_held(engine, gateway):
    _, body = pay_invoice(engine, gateway, "inv_1", "ach", "m_1", "key", now=100)
    assert handle_event(engine, failed_event(body["payment_id"]), now=NIGHT)["status"] == "failed"
