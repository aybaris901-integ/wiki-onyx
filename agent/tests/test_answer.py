import re

from brain.answer import clamp_sentences


def test_clamp_sentences():
    assert clamp_sentences("One. Two. Three. Four.") == "One. Two. Three."


def test_extractive_answer_has_owner_and_is_short(brain):
    import asyncio

    reply = asyncio.run(brain.answerer.ask("Why do payments go through a queue?"))
    assert len(re.split(r"(?<=[.!?])\s+", reply.answer.strip())) <= 3
    assert "Maya Okafor" in reply.answer
    assert "Priya Raman" in reply.answer
    types = [s.type for s in reply.sources]
    assert "owner" in types
    assert "pr" in types or "slack" in types
    assert all(s.url.startswith("https://") for s in reply.sources)
    assert reply.meta.model == "extractive"
    assert reply.meta.retriever == "chroma"


def test_owner_question(brain):
    import asyncio

    reply = asyncio.run(brain.answerer.ask("Who owns the image server?"))
    assert "Alex Chen" in reply.answer
    assert any(s.type == "owner" and s.author == "Alex Chen" for s in reply.sources)


def test_hybrid_search_prefers_relevant_docs(brain):
    hits = brain.index.search("double charged provider timed out", k=5)
    assert hits
    assert any("retry" in h.doc_id or "payments" in h.doc_id for h in hits[:2])
