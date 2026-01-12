import pytest

from app.charges import InvoiceAlreadyPaid, InvoiceNotFound, pay_invoice
from app.status import apply_status


def test_charges_invoice(engine, gateway):
    result = pay_invoice(engine, gateway, "inv_1", "card", now=100)
    assert result["status"] == "pending"
    assert len(gateway.charges) == 1


def test_unknown_invoice(engine, gateway):
    with pytest.raises(InvoiceNotFound):
        pay_invoice(engine, gateway, "nope", "card", now=100)


def test_paid_invoice_is_not_charged_again(engine, gateway):
    payment = pay_invoice(engine, gateway, "inv_1", "card", now=100)
    with engine.begin() as conn:
        apply_status(conn, payment["payment_id"], "succeeded", now=101)
    with pytest.raises(InvoiceAlreadyPaid):
        pay_invoice(engine, gateway, "inv_1", "card", now=102)
