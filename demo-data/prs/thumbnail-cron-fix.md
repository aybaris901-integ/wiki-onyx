---
type: pr
title: "Make thumbnail cron idempotent"
author: Alex Chen
date: 2026-08-12
branch: demo/thumbnail-cron-fix
files: [demo-data/acme/services/images/thumbnail_cron.py]
pr: thumbnail-cron-fix
url: null
---

## What

Lock file with O_EXCL so a second start exits immediately. Render to a temp name and rename so a crash never leaves a half-written thumbnail. Runbook section "how to run the thumbnail cron by hand".

## Why

The 01:00 deploy on 2026-08-12 restarted the cron mid-run. The second run's cleanup deleted renditions the first was still writing; a third of the storefront lost thumbnails (#images 2026-08-12). Two writers, no lock. This makes any number of overlapping starts safe.

Also: I was the only person who had ever run this by hand. Dana does a dry run next week.
