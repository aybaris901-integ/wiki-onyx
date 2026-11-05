---
type: handoff
title: "Checkout handover notes (Tomas Ruiz, leaving 2026-02-27)"
author: Tomas Ruiz
date: 2026-02-26
participants: [Tomas Ruiz, Priya Raman]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/handoffs/tomas-checkout-handover.md
pr: checkout-codeowners
---

# Checkout handover notes

Written for Priya Raman, who owns checkout and payments from 2026-03-02 (ADR 0004). The code is mine, the decisions were the team's. Every "why" below points at the thread or ADR where it was argued.

## What you now own

- services/checkout (cart.py, order.py): carts, orders, the hand-off to payments.
- services/payments (retry_queue.py, charge.py): Maya built the queue, you own it. Maya stays second reviewer.

## Things that look wrong but are not

1. **Prices are locked at add-to-cart time** (cart.py, CartLine.unit_price_cents). In 2021 a catalog price change mid-checkout charged customers more than the cart showed. Rule since then: the customer pays what they saw. Do not "fix" this to read live prices.
2. **Checkout never calls the payment provider.** It enqueues a charge (order.py, place_order). This is ADR 0001 after the 212 double charges. If someone proposes "just charge inline, it's faster", send them the incident review.
3. **Tax rounding is per line, then summed**, not rounded on the total. Finance asked for this in 2022 so our invoices match their ledger to the cent. It looks like a bug. It is a requirement.
4. **Idempotency key is the order id**, never attempt-specific. The whole retry queue depends on it.

## Open risks

- The retry queue worker is a single process. If it dies, charges queue up silently. Priya's queue-depth dashboard alerts at 500 jobs. Nobody has load-tested beyond 5k jobs.
- Express pay (flag checkout.express_pay) bypasses the cart page; the price lock still applies because it goes through Cart.add. Easy to break if someone refactors.

## Runbooks

- Stuck charge: find the job by order id in the retry_queue table, check attempts; if 5, the provider rejected it, contact them with the idempotency key.
- Provider outage: do nothing. The queue is the plan. Watch depth.

## People

- Maya Okafor knows the queue internals better than anyone.
- Jordan Lee has the LaunchDarkly and provider contracts.
