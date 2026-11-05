from brain.events import EventBus, event_from_webhook, has_why
from brain.models import Event


def test_has_why():
    assert has_why("## Why\nbecause customers were charged twice")
    assert has_why("We do this so that retries are safe")
    assert not has_why("Bump TTL to 3600.")
    assert not has_why("")


def test_pr_without_why_is_flagged():
    events = event_from_webhook("pr_merged", {"number": 9, "title": "Bump TTL", "author": "Alex Chen", "body": "Bump.", "url": "https://github.com/x/y/pull/9"})
    assert [e.type for e in events] == ["pr_merged", "pr_missing_why"]
    assert events[1].severity == "warn"
    assert events[1].sources[0].type == "pr"


def test_pr_with_why_is_not_flagged():
    events = event_from_webhook("pr_merged", {"number": 9, "title": "Queue", "body": "## Why\nDouble charges."})
    assert [e.type for e in events] == ["pr_merged"]


def test_ring_buffer_and_recent_order():
    bus = EventBus(size=3)
    for i in range(5):
        bus.emit(Event(type="info", title=str(i)))
    assert [e.title for e in bus.recent()] == ["4", "3", "2"]
