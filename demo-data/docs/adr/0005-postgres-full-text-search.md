---
type: adr
title: "ADR 0005: Search uses Postgres full text, not Elasticsearch"
author: Alex Chen
date: 2025-04-10
participants: [Alex Chen, Priya Raman, Dana Whitlock, Jordan Lee]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/adr/0005-postgres-full-text-search.md
pr: postgres-search
---

# ADR 0005: Search uses Postgres full text, not Elasticsearch

- **Status:** Accepted
- **Date:** 2025-04-10
- **Author:** Alex Chen
- **Owner:** Alex Chen (named successor: Priya Raman)

## Context

Product search over about 40k SKUs. Benchmarks (2025-04-08, #search): Postgres tsvector with a GIN index, p95 28 ms, p99 61 ms. Elasticsearch single node, p95 19 ms, p99 40 ms. Budget is 50 ms at p95. Both pass. We are six engineers.

## Decision

Postgres full-text search (services/search/indexer.py, services/search/query.py, {{pr:postgres-search}}). Weighted tsvector (title A, brand B, description C), GIN index, pg_trgm for simple typo tolerance, facets via GROUP BY.

"One less cluster to run" outweighs 9 ms at p95.

**Revisit trigger:** catalog grows 10x, or product needs real fuzzy ranking or faceting that GROUP BY cannot do under budget.

## Consequences

- No second cluster: no Elastic upgrades, backups, or reindex jobs.
- The search.elastic_backend flag exists but has no adapter behind it. It is a placeholder, not a feature.
- Search quality ceiling is lower than Elastic's. Accepted for now.
