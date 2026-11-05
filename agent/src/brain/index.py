"""Hybrid index: BM25 over every chunk (instant) + Chroma embeddings (persistent, lazy), fused with RRF.

`uv run python -m brain.index` rebuilds the Chroma collection from demo-data.
"""

from __future__ import annotations

import hashlib
import json
import os
import logging
import re
import threading
import time
from pathlib import Path
from typing import Callable, Sequence

from rank_bm25 import BM25Okapi

from .config import Settings, settings as default_settings
from .data import Chunk, Corpus

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
log = logging.getLogger("brain.index")

TOKEN = re.compile(r"[a-z0-9]+")
STOP = {
    "the", "a", "an", "is", "are", "was", "were", "do", "does", "did", "we", "our", "it", "to", "of", "in",
    "on", "for", "and", "or", "why", "how", "what", "who", "when", "where", "this", "that", "with", "still",
    "built", "way", "go", "goes", "through", "use", "run", "own", "now", "has", "have", "be", "by", "at",
}

Embedder = Callable[[Sequence[str]], list[list[float]]]


def tokenize(text: str) -> list[str]:
    words = TOKEN.findall(text.lower())
    out = []
    for w in words:
        if w in STOP:
            continue
        out.append(w)
        # crude stemming so "payments" matches "payment", "charged" matches "charge"
        for suffix in ("ing", "ed", "es", "s"):
            if len(w) > 4 and w.endswith(suffix):
                out.append(w[: -len(suffix)])
                break
    return out


def hash_embedder(texts: Sequence[str]) -> list[list[float]]:
    """Deterministic stand-in embedding (tests, or before the real model loads)."""
    vectors = []
    for text in texts:
        vec = [0.0] * 64
        for tok in tokenize(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % 64] += 1.0 if (h >> 8) % 2 else -1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        vectors.append([v / norm for v in vec])
    return vectors


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer  # heavy import, kept lazy

                started = time.time()
                self._model = SentenceTransformer(self.model_name)
                log.info("loaded %s in %.1fs", self.model_name, time.time() - started)
        return self._model

    @property
    def ready(self) -> bool:
        return self._model is not None

    def warm(self) -> None:
        self._load()

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        model = self._load()
        return model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False).tolist()


class HybridIndex:
    """BM25 is ready the moment the corpus loads; Chroma joins in once embeddings exist."""

    def __init__(self, corpus: Corpus, settings: Settings | None = None, embedder: Embedder | None = None):
        self.settings = settings or default_settings
        self.corpus = corpus
        self.embedder: Embedder = embedder or SentenceTransformerEmbedder(self.settings.embed_model)
        self.chunks = corpus.chunks
        self.by_id = {c.id: c for c in self.chunks}
        # titles count double so a PR named for the thing beats a doc that only mentions it
        self.bm25 = BM25Okapi([tokenize(c.title) * 2 + tokenize(c.text) for c in self.chunks] or [["empty"]])
        self.collection = None
        self._vector_ready = threading.Event()

    # ---------- chroma ----------

    def _fingerprint(self) -> str:
        raw = json.dumps(sorted((c.id, hashlib.md5(c.text.encode()).hexdigest()) for c in self.chunks))
        return hashlib.sha1(raw.encode()).hexdigest()

    def build_vectors(self, force: bool = False) -> int:
        """Create or reuse the persistent Chroma collection. Returns the number of vectors."""
        import chromadb

        self.settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.settings.chroma_dir))
        name = "company_brain"
        fingerprint = self._fingerprint()
        stamp = self.settings.chroma_dir / "fingerprint.txt"
        existing = client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})
        if not force and stamp.exists() and stamp.read_text().strip() == fingerprint and existing.count() == len(self.chunks):
            self.collection = existing
            self._vector_ready.set()
            log.info("chroma: reusing %d vectors", existing.count())
            return existing.count()
        client.delete_collection(name)
        collection = client.create_collection(name, metadata={"hnsw:space": "cosine"})
        batch = 64
        for start in range(0, len(self.chunks), batch):
            part = self.chunks[start:start + batch]
            collection.add(
                ids=[c.id for c in part],
                embeddings=self.embedder([c.text for c in part]),
                metadatas=[c.metadata() for c in part],
                documents=[c.text[:4000] for c in part],
            )
        stamp.write_text(fingerprint)
        self.collection = collection
        self._vector_ready.set()
        log.info("chroma: built %d vectors", collection.count())
        return collection.count()

    def build_vectors_in_background(self) -> threading.Thread:
        def run():
            try:
                self.build_vectors()
                warm = getattr(self.embedder, "warm", None)
                if warm:
                    warm()  # first question must not pay for loading the model
            except Exception as exc:  # the demo keeps working on BM25 alone
                log.warning("vector index unavailable: %s", exc)

        thread = threading.Thread(target=run, name="build-vectors", daemon=True)
        thread.start()
        return thread

    @property
    def vectors_ready(self) -> bool:
        """Vectors join the search only once the collection exists and the model is loaded, so no request blocks."""
        if not (self._vector_ready.is_set() and self.collection is not None):
            return False
        return getattr(self.embedder, "ready", True)

    # ---------- search ----------

    def keyword_search(self, query: str, k: int = 20) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)
        return [(self.chunks[i], float(scores[i])) for i in ranked[:k] if scores[i] > 0]

    def vector_search(self, query: str, k: int = 20) -> list[tuple[Chunk, float]]:
        if not self.vectors_ready or not self.chunks:
            return []
        try:
            result = self.collection.query(query_embeddings=self.embedder([query]), n_results=min(k, len(self.chunks)))
        except Exception as exc:
            log.warning("vector search failed: %s", exc)
            return []
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0] or [0.0] * len(ids)
        return [(self.by_id[i], 1.0 - float(d)) for i, d in zip(ids, distances) if i in self.by_id]

    def search(self, query: str, k: int = 12) -> list[Chunk]:
        """Reciprocal rank fusion of keyword and vector results, de-duplicated per document."""
        fused: dict[str, float] = {}
        for results, weight in ((self.keyword_search(query, k * 2), 1.0), (self.vector_search(query, k * 2), 1.0)):
            for rank, (chunk, _) in enumerate(results):
                fused[chunk.id] = fused.get(chunk.id, 0.0) + weight / (60 + rank)
        ordered = sorted(fused, key=fused.get, reverse=True)
        out: list[Chunk] = []
        seen_docs: dict[str, int] = {}
        for cid in ordered:
            chunk = self.by_id[cid]
            if seen_docs.get(chunk.doc_id, 0) >= 2:  # at most two chunks from one document
                continue
            seen_docs[chunk.doc_id] = seen_docs.get(chunk.doc_id, 0) + 1
            out.append(chunk)
            if len(out) >= k:
                break
        return out


def build(settings: Settings | None = None, force: bool = True) -> HybridIndex:
    settings = settings or default_settings
    corpus = Corpus(settings).load()
    index = HybridIndex(corpus, settings)
    count = index.build_vectors(force=force)
    print(f"indexed {len(corpus.chunks)} chunks from {settings.demo_data_dir} -> {count} vectors in {settings.chroma_dir}")
    for warning in corpus.warnings[:20]:
        print("warning:", warning)
    return index


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    build()
