"""Payment provider adapter.

Every call takes an idempotency key. The provider deduplicates on that key,
which is why the retry queue (retry_queue.py) can retry safely. Before
November 2025 this module retried inline on timeout, which is what caused the
212 double charges. That code is gone on purpose; do not add it back.

Owner: @priya.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol


class ProviderTimeout(Exception):
    """The provider did not answer. We do not know whether the charge happened."""


@dataclass(frozen=True)
class ChargeResult:
    idempotency_key: str
    amount_cents: int
    currency: str
    provider_ref: str


class Provider(Protocol):
    def charge(self, idempotency_key: str, amount_cents: int, currency: str) -> ChargeResult: ...


class FakeProvider:
    """Test double that times out some of the time, like the real one did in Nov 2025."""

    def __init__(self, timeout_rate: float = 0.0, seed: int = 0) -> None:
        self._timeout_rate = timeout_rate
        self._rng = random.Random(seed)
        self._seen: dict[str, ChargeResult] = {}
        self.charges_made = 0

    def charge(self, idempotency_key: str, amount_cents: int, currency: str) -> ChargeResult:
        if idempotency_key in self._seen:
            # Deduplicated by the provider: no second charge, same result back.
            return self._seen[idempotency_key]
        if self._rng.random() < self._timeout_rate:
            # The charge may or may not have gone through. That ambiguity is the
            # whole reason we never retry inline.
            raise ProviderTimeout(idempotency_key)
        self.charges_made += 1
        result = ChargeResult(
            idempotency_key, amount_cents, currency, provider_ref=f"ch_{self.charges_made:06d}"
        )
        self._seen[idempotency_key] = result
        return result
