import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, select

from . import config
from .charges import InvoiceAlreadyPaid, InvoiceNotFound, pay_invoice
from .db import payments
from .payrail import GatewayTimeout, PayRailClient


class PayRequest(BaseModel):
    method: str = "card"


def create_app(engine, gateway) -> FastAPI:
    app = FastAPI(title="payments-service")

    @app.post("/invoices/{invoice_id}/pay")
    def pay(invoice_id: str, request: PayRequest):
        try:
            return pay_invoice(engine, gateway, invoice_id, request.method, int(time.time()))
        except InvoiceNotFound:
            raise HTTPException(404, "invoice not found")
        except InvoiceAlreadyPaid:
            raise HTTPException(409, "invoice already paid")
        except GatewayTimeout:
            raise HTTPException(504, "payment gateway timed out")

    @app.get("/invoices/{invoice_id}/payment-status")
    def payment_status(invoice_id: str):
        with engine.connect() as conn:
            row = conn.execute(
                select(payments).where(payments.c.invoice_id == invoice_id).order_by(payments.c.updated_at.desc())
            ).mappings().first()
        if row is None:
            raise HTTPException(404, "no payment for this invoice")
        return {"payment_id": row["id"], "status": row["status"]}

    return app


def build() -> FastAPI:
    """Entry point: uvicorn app.main:build --factory"""
    return create_app(
        create_engine(config.DATABASE_URL),
        PayRailClient(config.PAYRAIL_BASE_URL, config.PAYRAIL_API_KEY),
    )
