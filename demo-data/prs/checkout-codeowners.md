---
type: pr
title: "CODEOWNERS: Priya owns checkout and payments"
author: Priya Raman
date: 2026-03-02
branch: demo/checkout-codeowners
files: [demo-data/acme/CODEOWNERS]
pr: checkout-codeowners
url: null
---

## What

Routes services/checkout and services/payments to @priya. Removes @tomas.

## Why

Tomas Ruiz left on 2026-03-01. Checkout and payments share a boundary (ADR 0001), so one owner. I had been primary reviewer on both since autumn (Jordan, #checkout 2026-02-25; eng weekly 2026-02-26; ADR 0004). Maya stays second reviewer on payments.

Read docs/handoffs/tomas-checkout-handover.md before touching the price lock or tax rounding.
