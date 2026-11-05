---
type: adr
title: "ADR 0004: Priya Raman owns checkout and payments"
author: Jordan Lee
date: 2026-03-02
participants: [Jordan Lee, Priya Raman, Tomas Ruiz, Maya Okafor]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/adr/0004-checkout-ownership.md
pr: checkout-codeowners
---

# ADR 0004: Priya Raman owns checkout and payments

- **Status:** Accepted
- **Date:** 2026-03-02
- **Author:** Jordan Lee

## Context

Tomas Ruiz, who wrote most of services/checkout and reviewed the payments retry queue, left Acme on 2026-03-01. Checkout and payments share a boundary (ADR 0001), so one owner is simpler than two. Priya Raman had been the primary reviewer for both since autumn 2025. See docs/meetings/2026-02-26-checkout-ownership.md and the #checkout thread of 2026-02-25.

## Decision

Priya Raman owns services/checkout and services/payments from 2026-03-02. CODEOWNERS updated in {{pr:checkout-codeowners}}. Maya Okafor remains second reviewer on payments while she works on fraud.

Tomas's handover notes (docs/handoffs/tomas-checkout-handover.md) are required reading before changing the price lock or tax rounding.

## Consequences

- Reviews, pages and decisions for checkout and payments route to Priya.
- The knowledge that was in Tomas's head is now in one document. Keep it current.
