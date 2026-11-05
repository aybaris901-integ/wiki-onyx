---
type: slack
title: "#images: thumbnails missing on the storefront (2am)"
author: Alex Chen
date: 2026-08-12
channel: "#images"
participants: [Alex Chen, Dana Whitlock, Jordan Lee]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/images-2026-08-12-thumbnail-outage.md
pr: thumbnail-cron-fix
---

**Alex Chen** (01:48): Paged. Storefront showing broken thumbnails on roughly a third of the catalog. Looking.

**Alex Chen** (02:05): Found it. The 01:00 deploy restarted the thumbnail cron mid-run. Cron started a second time, and the second run's cleanup step deleted renditions the first run was still writing. Two writers, no lock.

**Alex Chen** (02:21): Mitigation: killed both runs, re-rendering the missing thumbs now. Storefront should be clean in 20 minutes.

**Alex Chen** (02:44): Clean. Root cause fix: lock file with O_EXCL so a second start exits immediately, and write to a temp name then rename so a crash never leaves a half-written file. PR in the morning.

**Dana Whitlock** (08:15): Just seeing this. Sorry you were alone on it. Was the kill switch (images.hosted_cdn) an option?

**Alex Chen** (08:20): It would have served originals at full size, so the page would have loaded but slowly. Re-rendering was faster. Also: I'm the only one who has ever run the cron by hand. That's a problem.

**Jordan Lee** (09:02): Agreed, that's a problem. Alex, can you add a "how to run the thumbnail cron" section to the images runbook, and Dana, can you do a dry run of it next week so two people have done it?

**Dana Whitlock** (09:05): Yes.

**Alex Chen** (09:06): PR "Make thumbnail cron idempotent" is up. Runbook section added. Dana, I'll walk you through it Tuesday.
