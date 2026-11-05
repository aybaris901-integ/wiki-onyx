---
type: meeting
title: "Eng weekly: feature flags"
author: Jordan Lee
date: 2025-02-10
participants: [Jordan Lee, Priya Raman, Tomas Ruiz, Maya Okafor, Alex Chen, Dana Whitlock]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/meetings/2025-02-10-feature-flags.md
pr: feature-flags-json
---

## Context

Priya needs a flag for express pay. We have no flag system. LaunchDarkly quote from last quarter was more than the whole observability bill for a six-person team.

## Discussion

- Needs today: on/off per feature, know who flipped it and why, flip without a release train.
- A JSON file in the repo meets all three: git blame gives who, a required "why" field gives why, a one-line PR and a six-minute deploy flips it.
- Not needed today: percentage rollouts, per-customer targeting. Nobody could name a feature that needs them.

## Decisions

1. Feature flags live in config/feature_flags.json in the repo. No SaaS. Owner: Jordan Lee.
2. Every flag has a "why" field and an owner. A PR adding a flag without a why gets bounced.
3. Revisit when a feature genuinely needs percentage rollout or targeting.

## Actions

- Tomas: land the flag loader ({{pr:feature-flags-json}}).
- Jordan: ADR 0002.
