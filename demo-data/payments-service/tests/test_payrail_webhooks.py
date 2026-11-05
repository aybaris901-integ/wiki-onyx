import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import invoices, payments
from app.main import create_app
from app.payrail_webhooks import BadSignature, handle_event, verify_signature

SECRET = "whsec_test"


def sign(timestamp, body):
    return hmac.new(SECRET.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def test_valid_signature_passes():
    verify_signature(SECRET, "1000", b"{}", sign("1000", b"{}"), now=1010)


def test_tampered_body_fails():
    with pytest.raises(BadSignature):
        verify_signature(SECRET, "1000", b'{"a":1}', sign("1000", b"{}"), now=1010)


def test_old_timestamp_fails():
    with pytest.raises(BadSignature):
        verify_signature(SECRET, "1000", b"{}", sign("1000", b"{}"), now=2000)


def test_event_updates_payment_and_invoice(engine, pay):
    _, body = pay()
    event = {"id": "evt_1", "type": "payment.succeeded", "payment_id": body["payment_id"]}

    assert handle_event(engine, event, now=110)["status"] == "succeeded"

    with engine.connect() as conn:
        assert conn.execute(select(payments.c.status)).scalar_one() == "succeeded"
        assert conn.execute(select(invoices.c.status)).scalar_one() == "paid"


def test_redelivered_event_is_ignored(engine, pay):
    _, body = pay()
    event = {"id": "evt_1", "type": "payment.succeeded", "payment_id": body["payment_id"]}
    assert handle_event(engine, event, now=110) is not None
    assert handle_event(engine, event, now=111) is None


def test_route_rejects_bad_signature(engine, gateway):
    client = TestClient(create_app(engine, gateway, SECRET))
    response = client.post(
        "/webhooks/payrail",
        content=b"{}",
        headers={"x-payrail-timestamp": str(int(time.time())), "x-payrail-signature": "wrong"},
    )
    assert response.status_code == 401


def test_route_applies_signed_event(engine, gateway, pay):
    _, payment = pay()
    body = json.dumps({"id": "evt_1", "type": "payment.failed", "payment_id": payment["payment_id"]}).encode()
    timestamp = str(int(time.time()))
    client = TestClient(create_app(engine, gateway, SECRET))
    response = client.post(
        "/webhooks/payrail",
        content=body,
        headers={"x-payrail-timestamp": timestamp, "x-payrail-signature": sign(timestamp, body)},
    )
    assert response.status_code == 204
    with engine.connect() as conn:
        assert conn.execute(select(payments.c.status)).scalar_one() == "failed"
