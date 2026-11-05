"""Orders: the hand-off from checkout to payments.

Checkout never calls the payment provider. It writes the order and enqueues a
charge in the payments retry queue (services/payments/retry_queue.py). That
boundary is from ADR 0001; before it, checkout charged inline and a slow
provider meant double charges.

Owner: @priya (CODEOWNERS, 2026-03-02).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from ..payments.retry_queue import RetryQueue
from .cart import Cart


class OrderState(str, Enum):
    PLACED = "placed"
    CHARGE_PENDING = "charge_pending"
    PAID = "paid"
    FAILED = "failed"


@dataclass
class Order:
    order_id: str
    customer_id: str
    total_cents: int
    state: OrderState


def place_order(cart: Cart, queue: RetryQueue, order_id: str | None = None) -> Order:
    if cart.is_empty():
        raise ValueError("cannot place an order for an empty cart")
    order = Order(
        order_id=order_id or uuid.uuid4().hex,
        customer_id=cart.customer_id,
        total_cents=cart.subtotal_cents(),
        state=OrderState.PLACED,
    )
    # Enqueue, never charge. Idempotent on order_id, so a retry of this request
    # after a network blip still charges once.
    queue.enqueue(order.order_id, order.total_cents)
    order.state = OrderState.CHARGE_PENDING
    return order


def settle(order: Order, queue: RetryQueue) -> Order:
    """Called by the payments worker after a charge completes."""
    if order.order_id in queue.completed:
        order.state = OrderState.PAID
    return order
