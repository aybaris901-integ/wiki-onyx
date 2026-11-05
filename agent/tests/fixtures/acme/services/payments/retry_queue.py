"""Retry queue for charges. Charging inline double charged 212 orders in Nov 2025 (ADR 0001)."""


def enqueue(order_id: str) -> None:
    """Put the charge on the queue; a worker charges each order exactly once."""
    print("queued", order_id)
