"""question → retrieve → tools (author, discussion, owner) → LLM or template → AskResponse with sources."""

from __future__ import annotations

import logging
import re
import time

from . import llm
from .config import Settings, settings as default_settings
from .data import Chunk, Corpus
from .index import tokenize
from .models import AskMeta, AskResponse, Source
from .retrieve import Retriever

log = logging.getLogger("brain.answer")

SYSTEM = """You are Company Brain, the memory of a software company. A new hire asks why something is built
the way it is. Answer from the provided sources only. Always say WHO decided or built it, WHY, WHERE it was
discussed, and WHO owns it now (if an owner has left, say so and name the successor). Plain English, at most
three sentences, no bullet points, no markdown. Never invent names, dates or facts.

Reply with one JSON object and nothing else:
{"answer": "...", "sources": [{"id": "S1", "quote": "an exact line copied from that source that backs the answer"}]}
Cite 2 to 5 sources by their id. Quotes must be verbatim substrings of the source text, under 160 characters."""


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def clamp_sentences(text: str, limit: int = 3) -> str:
    return " ".join(_sentences(text)[:limit])


def _trim(text: str, limit: int = 160) -> str:
    """Cut at a sentence end, else at a word boundary, never mid-word."""
    text = text.strip().strip('"“”')
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for mark in (". ", "; ", ", "):
        pos = cut.rfind(mark)
        if pos > limit // 2:
            return cut[: pos + (1 if mark == ". " else 0)].strip()
    return cut[: cut.rfind(" ")].strip() + "…"


def overlap(query: str, text: str) -> int:
    return len(set(tokenize(query)) & set(tokenize(text)))


def best_line(chunk: Chunk, query: str) -> str | None:
    """The chunk line that shares the most words with the question, so the card shows a relevant quote."""
    candidates = [l for l in chunk.lines if l.strip().lower() != chunk.title.strip().lower() and not l.startswith("http")]
    best, score = None, -1
    for line in candidates:
        value = overlap(query, line)
        if value > score or (value == score and best and len(line) < len(best)):
            best, score = line, value
    return _trim(best) if best else None


def rank_for(query: str, chunks: list[Chunk], types: tuple[str, ...]) -> Chunk | None:
    """Among chunks of the given types, the one whose title (x3) and text overlap the question most."""
    scored = [(overlap(query, c.title) * 3 + overlap(query, c.text), -i, c) for i, c in enumerate(chunks) if c.type in types]
    if not scored:
        return None
    return max(scored, key=lambda t: (t[0], t[1]))[2]


def source_from(chunk: Chunk, quote: str | None = None, kind: str | None = None) -> Source:
    return Source(
        type=kind or chunk.source_type,
        url=chunk.url,
        author=chunk.author,
        date=chunk.date,
        title=chunk.title if chunk.type != "code" else None,
        quote=quote or None,
    )


class Answerer:
    def __init__(self, corpus: Corpus, retriever: Retriever, settings: Settings | None = None):
        self.corpus = corpus
        self.retriever = retriever
        self.settings = settings or default_settings

    # ---------- tools ----------

    def find_owner(self, chunks: list[Chunk]) -> tuple[Source | None, str]:
        """Current owner from CODEOWNERS for the code/PR files the evidence points at."""
        paths: list[str] = []
        for chunk in chunks:
            if chunk.type == "code":
                paths.append(chunk.path)
            if chunk.pr and chunk.pr in self.corpus.prs:
                paths.extend(self.corpus.prs[chunk.pr].files)
            paths.extend(chunk.files)
        for path in paths:
            owners = self.corpus.owners_for_path(path)
            if owners:
                owner = owners[0]
                note = f"{owner.name} owns it now."
                if owner.status == "left":
                    note = f"{owner.name} owned it but left on {owner.left or 'an unknown date'}; check the handoff doc."
                return (
                    Source(type="owner", url=self.corpus.settings.blob_url("demo-data/acme/CODEOWNERS"),
                           author=owner.name, date=owner.started or "", title=f"CODEOWNERS for {path}"),
                    note,
                )
        for chunk in chunks:  # an owner chunk retrieved directly ("who owns search?")
            if chunk.type == "owner" and chunk.people:
                person = self.corpus.person(chunk.people[0])
                return source_from(chunk, kind="owner"), f"{chunk.people[0]} owns it now." if not person or person.status != "left" else f"{chunk.people[0]} owned it but has left."
        return None, ""

    def find_discussion(self, chunks: list[Chunk]) -> list[Chunk]:
        return [c for c in chunks if c.type in ("slack", "meeting")]

    def find_code_author(self, chunks: list[Chunk]) -> list[Chunk]:
        return [c for c in chunks if c.type in ("pr", "code", "adr")]

    # ---------- main ----------

    async def ask(self, question: str) -> AskResponse:
        started = time.time()
        chunks = self.retriever.search(question, k=12)
        owner_source, owner_note = self.find_owner(chunks)
        model = "extractive"
        answer, sources = None, []

        if llm.available(self.settings) and chunks:
            try:
                answer, sources = await self._llm_answer(question, chunks, owner_note)
                model = self.settings.llm_name
            except Exception as exc:
                log.warning("llm failed, using extractive answer: %s", exc)

        if not answer:
            answer, sources = self._extractive(question, chunks, owner_note)

        if owner_source and not any(s.type == "owner" for s in sources):
            sources.append(owner_source)

        return AskResponse(
            answer=clamp_sentences(answer),
            sources=sources,
            meta=AskMeta(retriever=self.retriever.name, model=model, ms=int((time.time() - started) * 1000)),
        )

    async def _llm_answer(self, question: str, chunks: list[Chunk], owner_note: str) -> tuple[str, list[Source]]:
        labelled = []
        for i, chunk in enumerate(chunks, 1):
            labelled.append(
                f"[S{i}] type={chunk.type} title=\"{chunk.title}\" author={chunk.author or 'unknown'} "
                f"date={chunk.date or 'unknown'} url={chunk.url}\n{chunk.text[:1800]}"
            )
        user = f"Question: {question}\n\nWhat CODEOWNERS says today: {owner_note or 'no owner on record'}\n\nSources:\n\n" + "\n\n".join(labelled)
        reply = await llm.complete(SYSTEM, user, self.settings)
        data = llm.extract_json(reply or "")
        if not data or not str(data.get("answer", "")).strip():
            raise llm.LLMError("model did not return {answer, sources}")
        sources: list[Source] = []
        seen: set[str] = set()
        for item in data.get("sources") or []:
            if not isinstance(item, dict):
                continue
            match = re.search(r"(\d+)", str(item.get("id", "")))
            if not match or not 1 <= int(match.group(1)) <= len(chunks):
                continue
            chunk = chunks[int(match.group(1)) - 1]
            if chunk.doc_id in seen:
                continue
            seen.add(chunk.doc_id)
            quote = str(item.get("quote") or "").strip()
            if quote and quote.lower() not in chunk.text.lower():
                quote = best_line(chunk, question) or ""
            sources.append(source_from(chunk, quote[:160] or best_line(chunk, question)))
        if not sources:
            sources = [source_from(c, best_line(c, question)) for c in chunks[:3]]
        return str(data["answer"]).strip(), sources

    def _extractive(self, question: str, chunks: list[Chunk], owner_note: str) -> tuple[str, list[Source]]:
        if not chunks:
            return ("I couldn't find anything about that in the code, pull requests or Slack. Ask a person before you act.", [])
        parts: list[str] = []
        sources: list[Source] = []
        used: set[str] = set()

        def take(chunk: Chunk) -> str | None:
            if chunk.doc_id in used:
                return None
            used.add(chunk.doc_id)
            quote = best_line(chunk, question)
            sources.append(source_from(chunk, quote))
            return quote

        who_question = question.strip().lower().startswith("who")
        if who_question and owner_note:
            parts.append(owner_note)
            owner_note = ""
        built = rank_for(question, chunks, ("pr",)) or rank_for(question, chunks, ("adr", "code"))
        if built:
            quote = take(built)
            verb = "decided this" if built.type == "adr" else "built this"
            when = f" on {built.date}" if built.date else ""
            parts.append(f"{built.author or 'The team'} {verb} in “{built.title}”{when}" + (f": “{quote}”" if quote else "."))
        talk = rank_for(question, [c for c in chunks if c.doc_id not in used], ("slack", "meeting"))
        if talk:
            quote = take(talk)
            place = talk.channel or talk.title
            parts.append(f"It was discussed in {place}" + (f" on {talk.date}" if talk.date else "") + (f": “{quote}”" if quote else "."))
        if not parts:
            top = chunks[0]
            quote = take(top)
            parts.append(f"The closest record is {top.title} by {top.author or 'unknown'}" + (f": “{quote}”" if quote else "."))
        if owner_note:
            parts.append(owner_note)
        for chunk in chunks:
            if len(sources) >= 4:
                break
            if chunk.doc_id not in used and chunk.type in ("handoff", "issue", "adr", "code"):
                take(chunk)
        answer = " ".join(p if p.endswith((".", "”", "!", "?")) else p + "." for p in parts)
        return answer, sources
