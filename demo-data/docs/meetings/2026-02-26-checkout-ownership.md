---
type: meeting
title: "Eng weekly: checkout and payments ownership after Tomas"
author: Jordan Lee
date: 2026-02-26
participants: [Jordan Lee, Tomas Ruiz, Priya Raman, Maya Okafor, Alex Chen, Dana Whitlock]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/meetings/2026-02-26-checkout-ownership.md
pr: checkout-codeowners
---

## Context

Tomas Ruiz leaves on 2026-02-27 (last day). He wrote most of checkout and reviewed the payments retry queue. We need one named owner for both before Monday.

## Decisions

1. Priya Raman owns services/checkout and services/payments from 2026-03-02. CODEOWNERS updated that day ({{pr:checkout-codeowners}}).
2. Maya Okafor stays second reviewer on payments; she moves to fraud work for Q2.
3. Tomas's handover notes (docs/handoffs/tomas-checkout-handover.md) are the entry point for anyone touching checkout. Required reading before changing the price lock or tax rounding.
4. Jordan writes ADR 0004 to record the ownership change.

## Actions

- Priya: CODEOWNERS PR Monday 2026-03-02.
- Tomas: finish handover doc by Thursday.
- Jordan: ADR 0004, farewell lunch Friday.
