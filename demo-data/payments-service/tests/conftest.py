import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool

from app.db import invoices, metadata
from app.payrail import ChargeResult, GatewayTimeout


class FakeGateway:
    """Behaves like PayRail: a call that times out may still have charged the customer,
    and a repeated idempotency key returns the original payment instead of charging again."""

    def __init__(self, status="pending"):
        self.status = status
        self.charges = []
        self.timeouts_after_charging = 0
        self.statuses = {}
        self._by_key = {}

    def charge(self, *, idempotency_key, **kwargs):
        result = self._by_key.get(idempotency_key)
        if result is None:
            self.charges.append(kwargs)
            result = ChargeResult(payment_id=f"pay_{len(self.charges)}", status=self.status)
            self._by_key[idempotency_key] = result
        if self.timeouts_after_charging > 0:
            self.timeouts_after_charging -= 1
            raise GatewayTimeout("/payments")
        return result

    def get_payment(self, payment_id):
        return ChargeResult(payment_id=payment_id, status=self.statuses.get(payment_id, "pending"))


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            insert(invoices).values(id="inv_1", merchant_id="m_1", amount_cents=4820000, currency="USD", status="open")
        )
    return engine


@pytest.fixture
def gateway():
    return FakeGateway()


@pytest.fixture
def pay(engine, gateway):
    """Charge inv_1 by card with a fresh key unless one is given."""
    counter = {"n": 0}

    def _pay(key=None, invoice_id="inv_1", method="card", now=100):
        counter["n"] += 1
        return pay_invoice_(engine, gateway, invoice_id, method, "m_1", key or f"key_{counter['n']}", now)

    from app.charges import pay_invoice as pay_invoice_

    return _pay
