---
type: slack
title: "#eng: do we buy LaunchDarkly?"
author: Priya Raman
date: 2025-02-09
channel: "#eng"
participants: [Priya Raman, Jordan Lee, Maya Okafor, Tomas Ruiz]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/eng-2025-02-09-feature-flags.md
pr: feature-flags-json
---

**Priya Raman** (16:40): I want to ship express pay behind a flag. We have no flag system. Can we get LaunchDarkly?

**Jordan Lee** (16:45): I got a quote last quarter. For our seat count it's more than our whole observability bill. What do we actually need?

**Priya Raman** (16:47): On/off per feature, who turned it on, and a way to flip it without a full release.

**Tomas Ruiz** (16:50): A JSON file in the repo does the first two for free. Git blame tells you who and why. Flipping it is a one-line PR and a deploy, which is six minutes.

**Maya Okafor** (16:52): Percentage rollouts? Per-customer targeting?

**Tomas Ruiz** (16:53): Do we have a single feature that needs that today?

**Maya Okafor** (16:54): ...no.

**Jordan Lee** (16:58): Then JSON in the repo. Six engineers do not need a flag SaaS. Every flag gets a "why" field so the file explains itself. We revisit the day someone needs a percentage rollout.

**Priya Raman** (17:00): Fine by me, it unblocks me today. I'll put it on the agenda tomorrow so it's recorded.
