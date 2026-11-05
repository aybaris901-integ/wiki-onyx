---
type: slack
title: "#search: Elasticsearch or Postgres full text?"
author: Alex Chen
date: 2025-04-08
channel: "#search"
participants: [Alex Chen, Priya Raman, Dana Whitlock, Jordan Lee]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/search-2025-04-08-postgres-vs-elastic.md
pr: postgres-search
---

**Alex Chen** (11:03): Benchmarks for the new search are in. Postgres tsvector + GIN on the 40k product catalog: p95 28ms, p99 61ms. Elasticsearch single node: p95 19ms, p99 40ms. Elastic is faster. I still want Postgres.

**Priya Raman** (11:06): Why, if Elastic wins?

**Alex Chen** (11:08): Because 28ms is already under our 50ms budget, and Elastic is a second cluster: upgrades, backups, reindexing, a second thing to page on. We are six engineers. One less cluster to run is worth more than 9ms.

**Dana Whitlock** (11:10): Strongly agree from the infra side. Every cluster we add is a cluster I babysit.

**Priya Raman** (11:13): What about typo tolerance and facets? Product asked for "did you mean".

**Alex Chen** (11:16): pg_trgm covers simple typos. Facets we do with plain GROUP BY, the catalog is small. If we ever need real fuzzy ranking at 10x the catalog, that's the day we reopen this.

**Jordan Lee** (11:20): Write that trigger condition into the ADR so it's not a vibes decision later.

**Alex Chen** (11:21): Will do. ADR 0005. I'll leave the search.elastic_backend flag in place but off, no adapter behind it.

**Priya Raman** (11:24): OK, convinced. I'd like to pair on the GIN index migration though, I've never done one in prod.

**Alex Chen** (11:25): Thursday.
