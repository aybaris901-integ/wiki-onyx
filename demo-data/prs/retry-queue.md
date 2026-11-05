---
type: pr
title: "Move charges into a retry queue"
author: Maya Okafor
date: 2025-11-19
branch: demo/retry-queue
files: [demo-data/acme/services/payments/retry_queue.py, demo-data/acme/services/payments/charge.py, demo-data/acme/services/checkout/order.py]
pr: retry-queue
url: null
---

## What

Checkout no longer calls the payment provider. It writes the order and enqueues a charge job. A worker retries with backoff (1s, 5s, 30s, 2m, 10m) and then pages on-call. The idempotency key is `order:<order_id>` for every attempt.

## Why

Retrying inline is what double charged 212 orders last week. A provider timeout is an unknown, not a failure: the first charge may have succeeded. The only safe retry is one the provider can deduplicate, and the only safe place to do it is outside the request path.

Postgres SKIP LOCKED instead of Redis or SQS because we already run Postgres and this is an incident week (Tomas, #payments 2025-11-17). ADR 0001 has the full reasoning.

## Testing

FakeProvider with a 40% timeout rate, 10k orders: 10k charges, zero duplicates.

Reviewed by Tomas Ruiz.
