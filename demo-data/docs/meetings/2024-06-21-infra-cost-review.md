---
type: meeting
title: "Infra cost review: product images"
author: Dana Whitlock
date: 2024-06-21
participants: [Dana Whitlock, Alex Chen, Jordan Lee, Tomas Ruiz]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/meetings/2024-06-21-infra-cost-review.md
pr: self-hosted-images
---

## Context

Dana priced moving product images to a hosted image CDN (transforms + delivery). Catalog: 1.8M originals, 4 renditions each. Current cost: two image boxes plus storage.

## Numbers

- Hosted image CDN, monthly estimate at current volume: about 4x the cost of the two image boxes.
- Cost driver is per-transform billing, not egress.
- Traffic: about 9M image requests/day. Hosted pricing crosses over in our favour only if transforms are cached for 90+ days, which their plan does not allow at our tier.

## Decisions

1. Stay on the self-hosted image server. Owner: Alex Chen.
2. Keep the hosted CDN configured behind the images.hosted_cdn flag as a kill switch. Off by default. Owner: Dana Whitlock.
3. Revisit this decision if image traffic doubles (about 18M requests/day) or the team shrinks below the point where Alex can own it.
4. Alex writes the image server runbook by 2024-06-30.

## Actions

- Dana: write ADR 0003, ship flag and config ({{pr:self-hosted-images}}).
- Alex: runbook.
