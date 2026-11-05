---
type: adr
title: "ADR 0001: Charges go through a retry queue, never inline"
author: Tomas Ruiz
date: 2025-11-19
participants: [Tomas Ruiz, Maya Okafor, Priya Raman]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/adr/0001-payments-retry-queue.md
pr: retry-queue
---

# ADR 0001: Charges go through a retry queue, never inline

- **Status:** Accepted
- **Date:** 2025-11-19
- **Author:** Tomas Ruiz (decision), Maya Okafor (implementation)
- **Owner today:** Priya Raman (since 2026-03-02, see ADR 0004)

## Context

During the November 2025 sale the payment provider's p99 latency went to 14 s. Checkout called the provider inline, timed out at 10 s, and retried. Because a timeout does not tell you whether the charge happened, the retry charged the customer again. 212 orders were double charged. See the incident review (docs/meetings/2025-11-18-payments-incident-review.md) and the #payments thread of 2025-11-17.

## Decision

Checkout writes the order and enqueues a charge job in a Postgres-backed retry queue (services/payments/retry_queue.py, {{pr:retry-queue}}). A worker attempts the charge with exponential backoff. Every attempt for an order uses the same idempotency key (`order:<order_id>`), and the provider deduplicates on that key. After the fifth failed attempt the job stops and pages payments on-call.

No code may retry a provider call inline. The flag payments.retry_queue exists as documentation; turning it off is not supported.

## Consequences

- A payment can take seconds to minutes to settle; the order page shows "payment pending".
- One more table and one worker process. No new infrastructure (we chose Postgres SKIP LOCKED over Redis or SQS to avoid a new system during an incident).
- Double charges from timeouts are impossible by construction.

## Alternatives considered

- Show an error on timeout and do not retry: loses orders whose first charge succeeded.
- Redis or SQS queue: more infrastructure during an incident week.
