---
type: adr
title: "ADR 0002: Feature flags are a JSON file in the repo"
author: Jordan Lee
date: 2025-02-11
participants: [Jordan Lee, Tomas Ruiz, Priya Raman]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/adr/0002-feature-flags-in-repo.md
pr: feature-flags-json
---

# ADR 0002: Feature flags are a JSON file in the repo

- **Status:** Accepted
- **Date:** 2025-02-11
- **Author:** Jordan Lee
- **Owner:** Jordan Lee

## Context

We needed feature flags to ship express pay. A LaunchDarkly quote came to more than our entire observability bill for six engineers. Our real needs were on/off per feature, knowing who flipped it and why, and flipping without a release train. See docs/meetings/2025-02-10-feature-flags.md and the #eng thread of 2025-02-09.

## Decision

Flags live in config/feature_flags.json ({{pr:feature-flags-json}}). Each flag has `enabled`, `since`, `owner` and a required `why`. Changing a flag is a one-line PR plus a deploy (about six minutes). Git blame answers "who".

## Consequences

- No percentage rollouts or per-customer targeting. Revisit the day a feature needs one.
- Flag history is in git, which is better than most flag SaaS audit logs.
- Flipping a flag requires a deploy, so emergency flips take six minutes, not six seconds. Accepted.
