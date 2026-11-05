import pytest

from app.charges import InvoiceNotFound
from app.status import apply_status


def test_charges_invoice(pay, gateway):
    code, body = pay()
    assert code == 200 and body["status"] == "pending"
    assert len(gateway.charges) == 1


def test_unknown_invoice(pay):
    with pytest.raises(InvoiceNotFound):
        pay(invoice_id="nope")


def test_paid_invoice_is_not_charged_again(pay, engine, gateway):
    _, body = pay()
    with engine.begin() as conn:
        apply_status(conn, body["payment_id"], "succeeded", now=101)
    code, _ = pay()
    assert code == 409
    assert len(gateway.charges) == 1
