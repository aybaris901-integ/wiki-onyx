---
type: pr
title: "Product search on Postgres full text"
author: Alex Chen
date: 2025-04-11
branch: demo/postgres-search
files: [demo-data/acme/services/search/indexer.py, demo-data/acme/services/search/query.py]
pr: postgres-search
url: null
---

## What

Weighted tsvector (title A, brand B, description C) with a GIN index, pg_trgm for typos, GROUP BY facets. Indexer trigger on products, query module with ts_rank-shaped ranking.

## Why

Elasticsearch was 9 ms faster at p95 (19 vs 28 ms) and both are under the 50 ms budget. Elastic is a second cluster to upgrade, back up, reindex and page on, for six engineers. One less cluster to run is worth more than 9 ms (#search 2025-04-08, ADR 0005). Revisit at 10x catalog or when product needs real fuzzy ranking.

Priya paired on the GIN migration.
