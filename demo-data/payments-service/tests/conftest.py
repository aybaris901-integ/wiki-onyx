import itertools

import pytest
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool

from app.db import invoices, metadata
from app.payrail import ChargeResult, GatewayTimeout


class FakeGateway:
    """Behaves like PayRail: a call that times out may still have charged the customer."""

    def __init__(self, status="pending"):
        self.status = status
        self.charges = []
        self.timeouts_after_charging = 0
        self.statuses = {}
        self._ids = itertools.count(1)

    def charge(self, **kwargs):
        self.charges.append(kwargs)
        result = ChargeResult(payment_id=f"pay_{next(self._ids)}", status=self.status)
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
