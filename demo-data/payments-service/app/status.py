"""Single place where a payment's status changes."""
from sqlalchemy import select, update

from .db import invoices, payments


def apply_status(conn, payment_id: str, status: str, now: int) -> dict | None:
    """Record a new status. Returns an event for the merchant, or None if nothing changed."""
    row = conn.execute(select(payments).where(payments.c.id == payment_id)).mappings().first()
    if row is None or row["status"] == status:
        return None

    conn.execute(update(payments).where(payments.c.id == payment_id).values(status=status, updated_at=now))
    conn.execute(
        update(invoices)
        .where(invoices.c.id == row["invoice_id"])
        .values(status="paid" if status == "succeeded" else "open")
    )
    return {
        "merchant_id": row["merchant_id"],
        "invoice_id": row["invoice_id"],
        "payment_id": payment_id,
        "status": status,
    }
