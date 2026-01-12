"""Tells merchants' systems when a payment changes status."""
import time

import httpx
from sqlalchemy import select

from .db import merchant_endpoints

RETRY_INTERVAL_SECONDS = 60
MAX_ATTEMPTS = 5


def notify(engine, event: dict, post=httpx.post, sleep=time.sleep) -> bool:
    with engine.connect() as conn:
        endpoint = conn.execute(
            select(merchant_endpoints).where(merchant_endpoints.c.merchant_id == event["merchant_id"])
        ).mappings().first()
    if endpoint is None:
        return False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if post(endpoint["url"], json=event, timeout=5.0).status_code < 300:
                return True
        except httpx.HTTPError:
            pass
        if attempt < MAX_ATTEMPTS:
            sleep(RETRY_INTERVAL_SECONDS)
    return False
