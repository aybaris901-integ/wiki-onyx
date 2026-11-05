---
type: handoff
title: "Offboarding handoff: Alex Chen (images, search, thumbnail cron)"
author: Alex Chen
date: 2026-11-03
participants: [Alex Chen, Dana Whitlock, Priya Raman, Jordan Lee]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/handoffs/alex-offboarding.md
pr: thumbnail-cron-fix
---

# Offboarding handoff: Alex Chen

Prepared with Jordan in case I leave. Everything I own, who should take it, and the things that live only in my head.

## Systems I own

| System | Where | Takes over | State |
|---|---|---|---|
| Image server | services/images/server.py, two boxes img-1 and img-2 | **Dana Whitlock** | Stable. Cache hit rate about 94% since the TTL bump in Oct 2026. |
| Thumbnail cron | services/images/thumbnail_cron.py, nightly 01:00 | **Dana Whitlock** | Idempotent since Aug 2026 (lock file + rename). Dana has done one dry run. |
| Search indexer and query | services/search/ | **Priya Raman** | Stable. Postgres full text, ADR 0005. GIN index rebuilt quarterly. |
| images.hosted_cdn kill switch | config/feature_flags.json | Dana Whitlock | Configured, never flipped in prod. Test it once a year. |

## Why things are the way they are

- We run our own image server because hosted was 4x the cost (ADR 0003, #infra 2024-06-20). Revisit if traffic doubles. Current traffic is about 11M requests/day, so not yet.
- Search is Postgres not Elasticsearch because one less cluster to run (ADR 0005, #search 2025-04-08). Revisit at 10x catalog or when product needs real fuzzy ranking.
- The thumbnail cron has a lock file because two runs overlapped on 2026-08-12 and deleted each other's output (#images 2026-08-12, {{pr:thumbnail-cron-fix}}).

## Open risks

1. img-2 has a disk that reports SMART warnings since September. Dana knows. Replacement ordered.
2. The GIN index rebuild takes 40 minutes and locks writes to products. Only run it in the Sunday window.
3. The search.elastic_backend flag has no adapter. If someone flips it, search returns nothing. Delete the flag or write the adapter.

## Three things nobody else knows

1. **The thumbnail cron must not run while the catalog import runs** (Tuesdays 00:30 to 01:00). Import rewrites SKU ids for new products and the cron would render thumbnails for ids that are about to change. The 01:00 cron time was chosen for this reason, not by accident. It is not written down anywhere else.
2. **The image cache TTL was bumped to 24 h in October 2026 ({{pr:bump-image-cache-ttl}}) because img-1's CPU was pegged at 90% during the Prime Day week.** The PR body does not say this. If someone reverts it for "freshness", CPU goes back to 90%.
3. **pg_trgm similarity threshold is 0.28, set in a migration, not in code.** Product tuned it by hand in May 2025 for "did you mean". If search for typos suddenly gets worse after a database restore, check that setting first.

## Runbooks

- Thumbnails missing: check for a stale lock file at /var/run/acme-thumbnail-cron.lock, remove it only if no cron process is running, then run the cron by hand for the affected SKUs.
- Image server down: flip images.hosted_cdn to true, deploy (six minutes), fix the box, flip back.
- Search slow: check GIN index bloat; rebuild in the Sunday window.

## Who to ask

- Dana Whitlock for anything on the boxes.
- Priya Raman for search code. She paired on the GIN migration.
- Jordan Lee for the hosted CDN contract (still active, we pay the minimum).
