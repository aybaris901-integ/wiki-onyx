---
type: slack
title: Payments double charges during the sale
author: Tomas Ruiz
date: 2025-11-17
channel: "#payments"
participants: [Tomas Ruiz, Maya Okafor]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/payments-2025-11-17-retry-queue.md
pr: retry-queue
---
**Maya Okafor** (09:12): Support says customers were charged twice during the sale.
**Tomas Ruiz** (09:15): If the provider times out and we retry, we charge them again. It has to be a queue.
**Maya Okafor** (09:20): Agreed, I will move charges into a retry queue in {{pr:retry-queue}}.
