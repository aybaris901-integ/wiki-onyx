---
type: pr
title: "Feature flags as a JSON file in the repo"
author: Tomas Ruiz
date: 2025-02-12
branch: demo/feature-flags-json
files: [demo-data/acme/config/feature_flags.json]
pr: feature-flags-json
url: null
---

## What

Adds config/feature_flags.json and a loader. Each flag has enabled, since, owner, and a required why.

## Why

LaunchDarkly cost more than our observability bill for six engineers (Jordan, #eng 2025-02-09). We need on/off, who, and why. A file in git gives all three for free: blame is "who", the why field is "why", a one-line PR and a six-minute deploy is "flip it". Nobody could name a feature that needs percentage rollouts. ADR 0002.

Unblocks Priya's express pay.
