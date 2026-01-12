"""Charging an invoice."""
from sqlalchemy import insert, select

from .db import invoices, payments
from .payrail import GatewayTimeout

MAX_CHARGE_ATTEMPTS = 3


class InvoiceNotFound(Exception):
    pass


class InvoiceAlreadyPaid(Exception):
    pass


def pay_invoice(engine, gateway, invoice_id: str, method: str, now: int) -> dict:
    with engine.connect() as conn:
        invoice = conn.execute(select(invoices).where(invoices.c.id == invoice_id)).mappings().first()
    if invoice is None:
        raise InvoiceNotFound(invoice_id)
    if invoice["status"] == "paid":
        raise InvoiceAlreadyPaid(invoice_id)

    result = _charge_with_retry(gateway, invoice, method)

    with engine.begin() as conn:
        conn.execute(
            insert(payments).values(
                id=result.payment_id,
                invoice_id=invoice_id,
                merchant_id=invoice["merchant_id"],
                method=method,
                status=result.status,
                updated_at=now,
            )
        )
    return {"payment_id": result.payment_id, "status": result.status}


def _charge_with_retry(gateway, invoice, method):
    for attempt in range(1, MAX_CHARGE_ATTEMPTS + 1):
        try:
            return gateway.charge(
                amount_cents=invoice["amount_cents"],
                currency=invoice["currency"],
                reference=invoice["id"],
                method=method,
            )
        except GatewayTimeout:
            if attempt == MAX_CHARGE_ATTEMPTS:
                raise
