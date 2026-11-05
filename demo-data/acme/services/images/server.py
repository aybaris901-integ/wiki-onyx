"""Acme's own image server.

Why we run this instead of a hosted CDN: in June 2024 Dana Whitlock priced a
hosted image service and at our catalog size (1.8M originals, 4 renditions
each) it came to about four times what the two image boxes cost us. The team
agreed to revisit if traffic doubled. It has not. See ADR 0003
(docs/adr/0003-self-hosted-image-server.md) and the #infra thread from
2024-06-20. The feature flag images.hosted_cdn is the kill switch.

Owner: @alex. Alex also runs thumbnail_cron.py, which fills the cache this
server reads from.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

RENDITIONS = {"thumb": 160, "card": 480, "detail": 1200, "zoom": 2400}
CACHE_TTL_SECONDS = 86400  # bumped from 3600 in Oct 2026, PR "Bump image cache TTL"


@dataclass(frozen=True)
class ImageRequest:
    sku: str
    rendition: str

    def cache_key(self) -> str:
        if self.rendition not in RENDITIONS:
            raise KeyError(self.rendition)
        return hashlib.sha1(f"{self.sku}:{self.rendition}".encode()).hexdigest()


class ImageServer:
    def __init__(self, originals: Path, cache: Path) -> None:
        self._originals = originals
        self._cache = cache
        self.cache_hits = 0
        self.cache_misses = 0

    def path_for(self, request: ImageRequest) -> Path:
        cached = self._cache / f"{request.cache_key()}.webp"
        if cached.exists():
            self.cache_hits += 1
            return cached
        self.cache_misses += 1
        return self._render(request, cached)

    def _render(self, request: ImageRequest, target: Path) -> Path:
        # Real build shells out to libvips. Kept minimal here.
        source = self._originals / f"{request.sku}.jpg"
        if not source.exists():
            raise FileNotFoundError(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes()[: RENDITIONS[request.rendition]])
        return target

    def hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total else 0.0
