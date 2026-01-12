from fastapi.testclient import TestClient

from app.main import create_app

REQUEST = {"payment_id": "pay_1", "to": "ap@customer.example", "invoice_id": "inv_1", "amount_cents": 12500, "currency": "USD"}


def test_sends_receipt():
    sent = []
    response = TestClient(create_app(send=sent.append)).post("/internal/receipts", json=REQUEST)
    assert response.status_code == 202
    assert "125.00 USD" in sent[0].get_content()
