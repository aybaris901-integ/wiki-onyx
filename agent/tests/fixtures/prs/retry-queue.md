---
type: pr
title: Move charges into a retry queue
author: Maya Okafor
date: 2025-11-19
branch: maya/retry-queue
files: [demo-data/acme/services/payments/retry_queue.py]
pr: retry-queue
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/prs/retry-queue.md
---
## Why
Retrying inline is what double charged 212 orders last week. A queue charges each order exactly once.
