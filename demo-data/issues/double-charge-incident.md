---
type: issue
title: "Customers double charged during the November sale"
author: Tomas Ruiz
date: 2025-11-17
url: null
pr: retry-queue
---

40+ support tickets since Saturday: one order, two charges. Provider p99 is at 14 s, our charge call times out at 10 s and retries inline. 212 orders affected so far.

Fix: move charges into a retry queue with an idempotency key per order ({{pr:retry-queue}}). Inline retry disabled today.
