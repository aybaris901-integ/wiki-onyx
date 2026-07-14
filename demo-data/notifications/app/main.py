import time

from fastapi import FastAPI
from pydantic import BaseModel

from .outbox import enqueue


class ReceiptRequest(BaseModel):
    payment_id: str
    to: str
    invoice_id: str
    amount_cents: int
    currency: str


def create_app(engine) -> FastAPI:
    app = FastAPI(title="notifications")

    @app.post("/internal/receipts", status_code=202)
    def receipt(request: ReceiptRequest):
        payload = request.model_dump(exclude={"payment_id"})
        enqueue(engine, request.payment_id, payload, int(time.time()))
        return {"accepted": True}

    return app
