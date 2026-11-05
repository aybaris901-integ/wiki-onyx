---
type: adr
title: "ADR 0003: We run our own image server"
author: Dana Whitlock
date: 2024-06-24
participants: [Dana Whitlock, Alex Chen, Jordan Lee]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/adr/0003-self-hosted-image-server.md
pr: self-hosted-images
---

# ADR 0003: We run our own image server

- **Status:** Accepted (revisit if traffic doubles)
- **Date:** 2024-06-24
- **Author:** Dana Whitlock
- **Owner:** Alex Chen (image server and thumbnail cron), Dana Whitlock (kill switch and boxes)

## Context

A hosted image CDN would remove the image boxes and the thumbnail cron from our plate. Dana priced it in June 2024: at 1.8M originals with 4 renditions each, per-transform billing made it about four times the cost of our two image boxes. See docs/meetings/2024-06-21-infra-cost-review.md and the #infra thread of 2024-06-20.

## Decision

Keep the self-hosted image server (services/images/server.py) and nightly thumbnail cron. Keep the hosted CDN configured behind the images.hosted_cdn flag as a kill switch, off by default ({{pr:self-hosted-images}}).

**Revisit trigger:** image traffic doubles (about 18M requests/day), or nobody on the team can own the boxes.

## Consequences

- Someone owns two boxes and a cron. That is Alex Chen. A runbook is required (written 2024-06-28, expanded after the 2026-08-12 outage).
- If the image server fails, flipping images.hosted_cdn serves originals via the CDN at higher cost until fixed.
- Cost stays flat as the catalog grows; hosted cost would have grown with it.
