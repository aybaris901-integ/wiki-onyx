import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import idempotency
from app.db import idempotency_keys
from app.main import create_app
from app.payrail import GatewayTimeout


def test_same_key_charges_once_and_replays_the_answer(pay, gateway):
    first = pay(key="k1")
    second = pay(key="k1")
    assert first == second
    assert len(gateway.charges) == 1


def test_incident_replay_timeout_after_charging_does_not_double_charge(pay, gateway):
    """INC-2026-007: PayRail charged the card, then timed out, and we charged again on retry."""
    gateway.timeouts_after_charging = 1
    code, _ = pay(key="k1")
    assert code == 200
    assert len(gateway.charges) == 1


def test_declined_payment_is_replayed_and_needs_a_new_key(pay, gateway):
    gateway.status = "failed"
    assert pay(key="k1")[0] == 402
    assert pay(key="k1")[0] == 402
    assert len(gateway.charges) == 1

    gateway.status = "pending"
    assert pay(key="k2")[0] == 200
    assert len(gateway.charges) == 2


def test_key_used_for_a_different_request_is_rejected(pay):
    pay(key="k1", method="card")
    with pytest.raises(idempotency.KeyReused):
        pay(key="k1", method="ach")


def test_unknown_outcome_blocks_the_key(pay, gateway):
    """Every attempt timed out, so we can't tell if the customer was charged. See issue #10."""
    gateway.timeouts_after_charging = 3
    with pytest.raises(GatewayTimeout):
        pay(key="k1")
    with pytest.raises(idempotency.KeyInProgress):
        pay(key="k1")


def test_purge_only_removes_expired_keys(engine, pay):
    pay(key="old", now=100)
    assert idempotency.purge_expired(engine, now=100 + idempotency.RETENTION_SECONDS - 1) == 0
    assert idempotency.purge_expired(engine, now=100 + idempotency.RETENTION_SECONDS) == 1
    with engine.connect() as conn:
        assert conn.execute(select(idempotency_keys)).first() is None


def test_route_requires_a_key(engine, gateway):
    client = TestClient(create_app(engine, gateway, "secret"))
    response = client.post("/invoices/inv_1/pay", json={}, headers={"x-merchant-id": "m_1"})
    assert response.status_code == 400


def test_route_charges_and_replays(engine, gateway):
    client = TestClient(create_app(engine, gateway, "secret"))
    headers = {"x-merchant-id": "m_1", "idempotency-key": "k1"}
    assert client.post("/invoices/inv_1/pay", json={}, headers=headers).status_code == 200
    assert client.post("/invoices/inv_1/pay", json={}, headers=headers).status_code == 200
    assert len(gateway.charges) == 1


def test_route_does_not_charge_another_merchants_invoice(engine, gateway):
    client = TestClient(create_app(engine, gateway, "secret"))
    headers = {"x-merchant-id": "m_2", "idempotency-key": "k1"}
    assert client.post("/invoices/inv_1/pay", json={}, headers=headers).status_code == 404
    assert gateway.charges == []
