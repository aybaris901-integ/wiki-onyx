---
type: pr
title: "Keep the self-hosted image server, add hosted CDN kill switch"
author: Dana Whitlock
date: 2024-06-24
branch: demo/self-hosted-images
files: [demo-data/acme/services/images/server.py, demo-data/acme/config/feature_flags.json]
pr: self-hosted-images
url: null
---

## What

Wires the hosted image CDN config behind the images.hosted_cdn flag, off by default. Documents the decision in ADR 0003.

## Why

Hosted was about 4x the cost of our two image boxes at 1.8M originals x 4 renditions, because they bill per transform (#infra 2024-06-20, cost review 2024-06-21). We stay self-hosted and revisit if traffic doubles. The kill switch means an image server outage costs money for a week instead of a blank storefront.

Alex Chen owns the server and the cron. Runbook is on him.
