"""Charging an invoice."""
from sqlalchemy import insert, select

from . import idempotency
from .db import invoices, payments
from .payrail import GatewayTimeout

MAX_CHARGE_ATTEMPTS = 3


class InvoiceNotFound(Exception):
    pass


def pay_invoice(engine, gateway, invoice_id: str, method: str, merchant_id: str, key: str, now: int) -> tuple[int, dict]:
    """Returns (http status, body). The same key always gets the same answer and one charge."""
    with engine.connect() as conn:
        invoice = conn.execute(
            select(invoices).where(invoices.c.id == invoice_id, invoices.c.merchant_id == merchant_id)
        ).mappings().first()
    if invoice is None:
        raise InvoiceNotFound(invoice_id)

    hash_ = idempotency.request_hash(invoice_id, invoice["amount_cents"], invoice["currency"], method)
    replay = idempotency.claim(engine, merchant_id, key, hash_, now)
    if replay is not None:
        return replay

    if invoice["status"] == "paid":
        code, body = 409, {"detail": "invoice already paid"}
        idempotency.complete(engine, merchant_id, key, code, body)
        return code, body

    # If every attempt times out we don't know whether the customer was charged, so GatewayTimeout
    # propagates and the key stays in_progress. Further requests with this key get a 409 rather
    # than risk a second charge. Known gap: nothing clears these keys yet, see issue #10.
    result = _charge_with_retry(gateway, invoice, method, key)

    with engine.begin() as conn:
        conn.execute(
            insert(payments).values(
                id=result.payment_id,
                invoice_id=invoice_id,
                merchant_id=merchant_id,
                method=method,
                status=result.status,
                updated_at=now,
            )
        )
    code = 402 if result.status == "failed" else 200
    body = {"payment_id": result.payment_id, "status": result.status}
    idempotency.complete(engine, merchant_id, key, code, body)
    return code, body


def _charge_with_retry(gateway, invoice, method, key):
    # Retrying is only safe because PayRail receives the same idempotency key on every attempt.
    for attempt in range(1, MAX_CHARGE_ATTEMPTS + 1):
        try:
            return gateway.charge(
                amount_cents=invoice["amount_cents"],
                currency=invoice["currency"],
                reference=invoice["id"],
                method=method,
                idempotency_key=key,
            )
        except GatewayTimeout:
            if attempt == MAX_CHARGE_ATTEMPTS:
                raise
