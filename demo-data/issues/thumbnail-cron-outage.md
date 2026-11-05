---
type: issue
title: "Thumbnails missing on a third of the storefront (2026-08-12)"
author: Alex Chen
date: 2026-08-12
url: null
pr: thumbnail-cron-fix
---

Deploy restarted the thumbnail cron mid-run; two overlapping runs deleted each other's output. Mitigated at 02:44 by re-rendering. Fix: lock file plus atomic rename ({{pr:thumbnail-cron-fix}}). Follow-up: a second person must know how to run the cron by hand.
