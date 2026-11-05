"""Wire types shared by the API, the answerer and the event feed. Mirrors AGENTS.md."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SourceType = Literal["pr", "slack", "commit", "code", "doc", "owner", "issue"]


class Source(BaseModel):
    type: str
    url: str
    author: str = ""
    date: str = ""
    title: str | None = None
    quote: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AskMeta(BaseModel):
    retriever: str
    model: str
    ms: int
    live: bool = True


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    meta: AskMeta


EventType = Literal[
    "employee_left",
    "handoff_report",
    "new_hire",
    "onboarding_plan",
    "pr_merged",
    "pr_missing_why",
    "info",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Event(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:10]}")
    type: str
    title: str
    body: str = ""
    at: str = Field(default_factory=now_iso)
    person: str | None = None
    sources: list[Source] = Field(default_factory=list)
    severity: Literal["info", "warn", "good"] = "info"


class EventIn(BaseModel):
    type: str
    payload: dict = Field(default_factory=dict)


class Person(BaseModel):
    name: str
    handle: str
    email: str = ""
    role: str = ""
    team: str = ""
    status: str = "active"
    started: str = ""
    left: str = ""
    manager: str = ""


class StatusIn(BaseModel):
    status: Literal["left", "active", "new"]
