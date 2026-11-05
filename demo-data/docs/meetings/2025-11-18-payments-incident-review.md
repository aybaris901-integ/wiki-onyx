---
type: meeting
title: "Incident review: double charges during the November sale"
author: Priya Raman
date: 2025-11-18
participants: [Priya Raman, Maya Okafor, Tomas Ruiz, Jordan Lee, Dana Whitlock]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/meetings/2025-11-18-payments-incident-review.md
pr: retry-queue
---

## What happened

From 2025-11-15 to 2025-11-17 the payment provider's p99 latency rose from 800 ms to about 14 s. Our charge call timed out at 10 s. The checkout code caught the timeout and retried the charge inline. In most cases the first charge had actually succeeded, so the retry charged the customer a second time.

**212 orders were double charged.** All refunded by 2025-11-17 evening. 40+ support tickets.

## Why it happened

A timeout is not a failure. It is an unknown: the charge may or may not have gone through. The old code treated it as a failure and retried, which is only safe if the first attempt definitely did not happen.

## What we are changing

Charges move out of the request path into a retry queue (Postgres table, SKIP LOCKED worker). Each order gets one idempotency key, the provider deduplicates on it, and retries are safe. Maya Okafor is building it; Tomas Ruiz reviews.

## Decisions

1. No inline retries against the payment provider, ever. Already disabled as of 2025-11-17.
2. All charges go through the retry queue ({{pr:retry-queue}}). Owner: Maya Okafor (builder), Payments team.
3. Idempotency key = order id, never per attempt.
4. After five backoff attempts the job stops and pages payments on-call rather than retrying forever.

## Actions

- Maya: queue PR by 2025-11-19.
- Tomas: review, ADR 0001.
- Priya: this document, and a dashboard for queue depth.
