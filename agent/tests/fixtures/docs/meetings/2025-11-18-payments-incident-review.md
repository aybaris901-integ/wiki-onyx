---
type: meeting
title: Payments incident review
author: Jordan Lee
date: 2025-11-18
participants: [Jordan Lee, Maya Okafor, Tomas Ruiz]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/meetings/2025-11-18-payments-incident-review.md
---
## Summary
212 orders were double charged when the payment provider timed out.

## Decisions
- Charges go through a retry queue, never inline.
