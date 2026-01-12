import logging

from fastapi import FastAPI
from pydantic import BaseModel

from .mailer import build_receipt, send_smtp

log = logging.getLogger("notifications")


class ReceiptRequest(BaseModel):
    payment_id: str
    to: str
    invoice_id: str
    amount_cents: int
    currency: str


def create_app(send=send_smtp) -> FastAPI:
    app = FastAPI(title="notifications")

    @app.post("/internal/receipts", status_code=202)
    def receipt(request: ReceiptRequest):
        try:
            send(build_receipt(request.to, request.invoice_id, request.amount_cents, request.currency))
        except OSError:
            log.exception("could not send receipt for %s", request.payment_id)
        return {"accepted": True}

    return app
