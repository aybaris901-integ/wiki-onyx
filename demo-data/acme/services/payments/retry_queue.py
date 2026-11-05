"""Retry queue for customer charges.

Why this exists: during the November 2025 sale the payment provider started
timing out. The old code retried the charge inline, inside the request, and
212 orders were charged twice. See ADR 0001
(docs/adr/0001-payments-retry-queue.md) and PR "Move charges into a retry
queue" by Maya Okafor, 2025-11-19.

The rule: a charge is enqueued once, keyed by order id. Workers retry with
backoff, and the provider call is idempotent on that key, so a timeout can
never produce a second charge.

Owner: @priya (since 2026-03-02; Maya built it, Priya owns it).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .charge import ChargeResult, Provider, ProviderTimeout

BACKOFF_SECONDS = (1, 5, 30, 120, 600)


@dataclass
class ChargeJob:
    order_id: str
    amount_cents: int
    currency: str
    attempts: int = 0
    next_run_at: float = field(default_factory=time.time)

    @property
    def idempotency_key(self) -> str:
        # One key per order, never per attempt. This is the whole fix.
        return f"order:{self.order_id}"


class RetryQueue:
    """In-process queue. Production uses the same class over Postgres SKIP LOCKED."""

    def __init__(self, provider: Provider) -> None:
        self._provider = provider
        self._jobs: dict[str, ChargeJob] = {}
        self.completed: dict[str, ChargeResult] = {}

    def enqueue(self, order_id: str, amount_cents: int, currency: str = "USD") -> ChargeJob:
        if order_id in self._jobs or order_id in self.completed:
            # Enqueueing twice is a no-op. Checkout can call this freely.
            return self._jobs.get(order_id) or ChargeJob(order_id, amount_cents, currency)
        job = ChargeJob(order_id, amount_cents, currency)
        self._jobs[order_id] = job
        return job

    def run_once(self, now: float | None = None) -> int:
        """Attempt every due job once. Returns the number of jobs attempted."""
        now = time.time() if now is None else now
        attempted = 0
        for job in list(self._jobs.values()):
            if job.next_run_at > now:
                continue
            attempted += 1
            try:
                result = self._provider.charge(
                    job.idempotency_key, job.amount_cents, job.currency
                )
            except ProviderTimeout:
                self._reschedule(job, now)
                continue
            self.completed[job.order_id] = result
            del self._jobs[job.order_id]
        return attempted

    def _reschedule(self, job: ChargeJob, now: float) -> None:
        job.attempts += 1
        if job.attempts >= len(BACKOFF_SECONDS):
            # After the last backoff we stop retrying and page payments on-call.
            job.next_run_at = float("inf")
            return
        job.next_run_at = now + BACKOFF_SECONDS[job.attempts]

    def pending(self) -> list[ChargeJob]:
        return sorted(self._jobs.values(), key=lambda j: j.next_run_at)
