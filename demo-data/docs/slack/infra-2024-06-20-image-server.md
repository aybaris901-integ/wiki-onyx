---
type: slack
title: "#infra: hosted CDN vs our own image server"
author: Dana Whitlock
date: 2024-06-20
channel: "#infra"
participants: [Dana Whitlock, Alex Chen, Jordan Lee, Tomas Ruiz]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/infra-2024-06-20-image-server.md
pr: self-hosted-images
---

**Dana Whitlock** (14:02): Finished the pricing exercise for moving product images to a hosted image CDN. Short version: at our catalog size it's about 4x what the two image boxes cost us per month. Numbers in the meeting doc tomorrow.

**Alex Chen** (14:05): 4x is a lot. What's driving it, transforms or egress?

**Dana Whitlock** (14:07): Transforms. 1.8M originals times 4 renditions, and they bill per transform per month. Egress alone would be fine.

**Jordan Lee** (14:10): What do we lose by staying self-hosted?

**Alex Chen** (14:12): Someone has to own the boxes and the thumbnail cron. That's me. It's maybe two hours a month unless something breaks.

**Tomas Ruiz** (14:15): "Unless something breaks" is the expensive part. What happens when Alex is on holiday?

**Alex Chen** (14:17): Fair. I'll write a runbook. And Dana, can we keep the hosted CDN wired up behind a flag as a kill switch, so if the image server dies we flip it and eat the cost for a week?

**Dana Whitlock** (14:19): Yes, that's cheap. Flag off by default, config ready.

**Jordan Lee** (14:22): Proposal: stay self-hosted, keep the kill switch, and we revisit if traffic doubles. Objections?

**Tomas Ruiz** (14:23): None, as long as the runbook exists.

**Dana Whitlock** (14:24): Agreed. I'll write it up as ADR 0003 and ship the flag + config Monday.

**Alex Chen** (14:25): Runbook by end of month. Famous last words.
