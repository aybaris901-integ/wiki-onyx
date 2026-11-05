"""Triggerware-style event feed: ring buffer + asyncio fan-out for SSE, and the PR 'why' check."""

from __future__ import annotations

import asyncio
import re
from collections import deque

from .models import Event, Source

WHY = re.compile(r"\bbecause\b|\bwhy\b|\bso that\b|\bcontext\b|\bmotivation\b|\brationale\b|^##+\s*why", re.I | re.M)


def has_why(body: str | None) -> bool:
    return bool(body) and bool(WHY.search(body))


class EventBus:
    def __init__(self, size: int = 50):
        self.events: deque[Event] = deque(maxlen=size)
        self.subscribers: set[asyncio.Queue] = set()

    def recent(self) -> list[Event]:
        return list(reversed(self.events))

    def emit(self, event: Event) -> Event:
        self.events.append(event)
        for queue in list(self.subscribers):
            queue.put_nowait(event)
        return event

    def clear(self) -> None:
        self.events.clear()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self.subscribers.discard(queue)

    async def stream(self):
        """Async generator of SSE frames. Sends a comment every 15 s to keep proxies awake."""
        queue = self.subscribe()
        try:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield f"id: {event.id}\nevent: {event.type}\ndata: {event.model_dump_json()}\n\n"
        finally:
            self.unsubscribe(queue)


def event_from_webhook(kind: str, payload: dict) -> list[Event]:
    """Turns an inbound webhook (Triggerware GitHub connector, or the simulator) into events."""
    events: list[Event] = []
    if kind == "pr_merged":
        title = str(payload.get("title") or f"PR #{payload.get('number', '?')}")
        url = str(payload.get("url") or "")
        author = str(payload.get("author") or "")
        number = payload.get("number")
        source = Source(type="pr", url=url, author=author, date=str(payload.get("merged_at") or payload.get("date") or ""), title=title)
        events.append(Event(type="pr_merged", title=f"Merged: {title}", body=f"PR #{number} by {author} was merged." if number else f"{title} was merged.", person=author or None, sources=[source] if url else [], severity="info"))
        if not has_why(str(payload.get("body") or "")):
            events.append(Event(
                type="pr_missing_why",
                title=f"PR #{number} merged without a why" if number else f"“{title}” merged without a why",
                body=(f"{author or 'The author'} merged **{title}** with no explanation of why. "
                      "Six months from now nobody will know. Ask for a one-line reason in the PR body."),
                person=author or None,
                sources=[source] if url else [],
                severity="warn",
            ))
    else:
        events.append(Event(
            type=kind if kind in Event.model_fields["type"].annotation.__args__ else "info",
            title=str(payload.get("title") or kind.replace("_", " ").capitalize()),
            body=str(payload.get("body") or ""),
            person=payload.get("person"),
            severity=payload.get("severity", "info") if payload.get("severity") in ("info", "warn", "good") else "info",
        ))
    return events
