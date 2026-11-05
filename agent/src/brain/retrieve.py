"""Retriever protocol: Chroma/BM25 hybrid by default, Onyx when ONYX_URL is set (falls back on any error)."""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from .config import Settings, settings as default_settings
from .data import Chunk
from .index import HybridIndex

log = logging.getLogger("brain.retrieve")


class Retriever(Protocol):
    name: str

    def search(self, query: str, k: int = 12) -> list[Chunk]: ...


class ChromaRetriever:
    name = "chroma"

    def __init__(self, index: HybridIndex):
        self.index = index

    def search(self, query: str, k: int = 12) -> list[Chunk]:
        return self.index.search(query, k)


class OnyxRetriever:
    """Asks a self-hosted Onyx for documents, then maps them back onto our chunks by url/title.

    Onyx exposes a document search at POST /api/query/document-search (admin API) and chat at
    POST /api/chat/send-message. We use document search and only keep results we can map to a known
    document so the frontend's cards still carry author/date/type. Anything unexpected → Chroma.
    """

    name = "onyx"

    def __init__(self, index: HybridIndex, settings: Settings | None = None):
        self.settings = settings or default_settings
        self.index = index
        self.fallback = ChromaRetriever(index)

    def _headers(self) -> dict:
        headers = {"content-type": "application/json"}
        if self.settings.onyx_api_key:
            headers["authorization"] = f"Bearer {self.settings.onyx_api_key}"
        return headers

    def search(self, query: str, k: int = 12) -> list[Chunk]:
        try:
            response = httpx.post(
                f"{self.settings.onyx_url}/api/query/document-search",
                json={"message": query, "search_type": "hybrid", "retrieval_options": {"limit": k}},
                headers=self._headers(),
                timeout=8.0,
            )
            response.raise_for_status()
            docs = response.json().get("top_documents") or []
        except Exception as exc:
            log.warning("onyx unavailable (%s); using chroma", exc)
            return self.fallback.search(query, k)

        found: list[Chunk] = []
        by_url = {c.url.split("#")[0]: c for c in self.index.chunks}
        by_title = {c.title.lower(): c for c in self.index.chunks}
        for doc in docs:
            link = (doc.get("link") or "").split("#")[0]
            title = (doc.get("semantic_identifier") or "").lower()
            chunk = by_url.get(link) or by_title.get(title)
            if chunk and chunk not in found:
                found.append(chunk)
        if len(found) < 3:  # Onyx answered but we could not map enough of it
            for chunk in self.fallback.search(query, k):
                if chunk not in found:
                    found.append(chunk)
        return found[:k]


def make_retriever(index: HybridIndex, settings: Settings | None = None) -> Retriever:
    settings = settings or default_settings
    if settings.onyx_url:
        return OnyxRetriever(index, settings)
    return ChromaRetriever(index)
