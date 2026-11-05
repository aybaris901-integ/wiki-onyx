from brain.data import Corpus, parse_front_matter


def test_front_matter_parses():
    meta, body = parse_front_matter("---\ntype: slack\ntitle: Hi\n---\nbody here\n")
    assert meta == {"type": "slack", "title": "Hi"}
    assert body.strip() == "body here"


def test_corpus_loads_everything(settings):
    corpus = Corpus(settings).load()
    types = {c.type for c in corpus.chunks}
    assert {"slack", "meeting", "adr", "handoff", "pr", "issue", "code", "owner"} <= types
    assert len(corpus.people) == 7
    assert corpus.person("alex").name == "Alex Chen"
    assert corpus.person("Priya Raman").handle == "priya"


def test_pr_template_renders_search_url_when_unseeded(settings):
    corpus = Corpus(settings).load()
    thread = corpus.docs["demo-data/docs/slack/payments-2025-11-17-retry-queue.md"]
    assert "{{pr:" not in thread.text
    assert "PR “Move charges into a retry queue”" in thread.text
    assert "pulls?q=Move+charges" in thread.text


def test_pr_template_renders_number_when_seeded(settings):
    corpus = Corpus(settings).load()
    adr = corpus.docs["demo-data/docs/adr/0003-self-hosted-image-server.md"]
    assert corpus.pr_url(corpus.prs["self-hosted-images"]).endswith("/pull/7")
    assert adr.pr == "self-hosted-images"


def test_codeowners_and_code_author(settings):
    corpus = Corpus(settings).load()
    owners = corpus.owners_for_path("demo-data/acme/services/payments/retry_queue.py")
    assert [o.name for o in owners] == ["Priya Raman"]
    code = corpus.docs["demo-data/acme/services/payments/retry_queue.py"]
    assert code.author == "Maya Okafor"  # from the PR's files in the manifest
    assert code.pr == "retry-queue"
    assert code.url.endswith("demo-data/acme/services/payments/retry_queue.py")


def test_person_evidence(settings):
    corpus = Corpus(settings).load()
    alex = corpus.person("alex")
    assert corpus.handoff_doc(alex) is not None
    assert "services/images/" in corpus.owned_paths(alex)
