"""Search queries over the Postgres full-text index (see indexer.py, ADR 0005).

Ranking is the Postgres ts_rank shape: sum of matched term weights, with a
small boost for matching every term. Good enough for 40k SKUs; if we ever
need typo tolerance or facets at scale, that is the moment to reopen the
Elasticsearch question. Alex Chen, 2025-04-10.

Owner: @alex.
"""

from __future__ import annotations

from dataclasses import dataclass

from .indexer import Index, Product, tokens


@dataclass(frozen=True)
class Hit:
    product: Product
    rank: float


def search(index: Index, query: str, limit: int = 20) -> list[Hit]:
    terms = tokens(query)
    if not terms:
        return []
    hits: list[Hit] = []
    for sku, vector in index._vectors.items():  # noqa: SLF001  (same module family)
        matched = [vector[t] for t in terms if t in vector]
        if not matched:
            continue
        rank = sum(matched)
        if len(matched) == len(terms):
            rank *= 1.5  # all terms present, like plainto_tsquery with &
        hits.append(Hit(index.products[sku], rank))
    hits.sort(key=lambda h: (-h.rank, h.product.sku))
    return hits[:limit]
