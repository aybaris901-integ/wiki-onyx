"""Search indexer: Postgres full-text, not Elasticsearch.

Why: in April 2025 Alex Chen compared the two for our catalog (about 40k
products). Postgres tsvector with a GIN index answered in under 30 ms at p95,
and it meant "one less cluster to run" for a team of six. See ADR 0005
(docs/adr/0005-postgres-full-text-search.md) and the #search thread from
2025-04-08. The search.elastic_backend flag exists but the adapter was never
written.

Owner: @alex. Priya is the named successor (docs/handoffs/alex-offboarding.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TOKEN = re.compile(r"[a-z0-9]+")

# Weighted the way the SQL does it: setweight(to_tsvector(title), 'A') || ... (description, 'C')
WEIGHTS = {"title": 1.0, "brand": 0.8, "description": 0.4}


@dataclass(frozen=True)
class Product:
    sku: str
    title: str
    brand: str
    description: str


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def to_tsvector(product: Product) -> dict[str, float]:
    """A tiny stand-in for Postgres to_tsvector so tests can run without a database."""
    vector: dict[str, float] = {}
    for field_name, weight in WEIGHTS.items():
        for token in tokens(getattr(product, field_name)):
            vector[token] = vector.get(token, 0.0) + weight
    return vector


class Index:
    def __init__(self) -> None:
        self._vectors: dict[str, dict[str, float]] = {}
        self.products: dict[str, Product] = {}

    def upsert(self, product: Product) -> None:
        # Mirrors the UPDATE ... SET search_vector = to_tsvector(...) trigger in Postgres.
        self.products[product.sku] = product
        self._vectors[product.sku] = to_tsvector(product)

    def delete(self, sku: str) -> None:
        self.products.pop(sku, None)
        self._vectors.pop(sku, None)

    def vector(self, sku: str) -> dict[str, float]:
        return self._vectors[sku]
