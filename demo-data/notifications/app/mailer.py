import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
FROM_ADDRESS = "receipts@acme.example"


def build_receipt(to: str, invoice_id: str, amount_cents: int, currency: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = FROM_ADDRESS
    message["To"] = to
    message["Subject"] = f"Receipt for invoice {invoice_id}"
    message.set_content(f"We received your payment of {amount_cents / 100:.2f} {currency} for invoice {invoice_id}.")
    return message


def send_smtp(message: EmailMessage) -> None:
    with smtplib.SMTP(SMTP_HOST, timeout=10) as smtp:
        smtp.send_message(message)
