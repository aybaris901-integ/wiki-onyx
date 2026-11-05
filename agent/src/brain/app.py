"""FastAPI app: /ask, /health, /events, /roster. Run with `uv run uvicorn brain.app:app --port 8000`."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .answer import Answerer
from .config import Settings, settings as default_settings
from .data import Corpus
from .events import EventBus, event_from_webhook
from .index import Embedder, HybridIndex
from .models import AskRequest, AskResponse, Event, EventIn, Source, StatusIn
from .retrieve import make_retriever
from .roster import Roster

log = logging.getLogger("brain.app")


class Brain:
    """Everything the routes need, built once at startup (or by tests with a fixture dataset)."""

    def __init__(self, settings: Settings | None = None, embedder: Embedder | None = None, vectors: str = "background"):
        self.settings = settings or default_settings
        self.corpus = Corpus(self.settings).load()
        self.index = HybridIndex(self.corpus, self.settings, embedder=embedder)
        if vectors == "now":
            self.index.build_vectors()
        elif vectors == "background":
            self.index.build_vectors_in_background()
        self.retriever = make_retriever(self.index, self.settings)
        self.answerer = Answerer(self.corpus, self.retriever, self.settings)
        self.roster = Roster(self.corpus, self.settings)
        self.events = EventBus()
        self.tasks: set[asyncio.Task] = set()
        self.started = time.time()

    def spawn(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task


class RateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window = self.hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.per_minute:
            return False
        window.append(now)
        return True


def create_app(settings: Settings | None = None, brain: Brain | None = None) -> FastAPI:
    settings = settings or default_settings

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.brain is None:
            app.state.brain = Brain(settings)
        brain: Brain = app.state.brain
        log.info("company brain up: %d chunks, retriever=%s, llm=%s", len(brain.corpus.chunks), brain.retriever.name, settings.llm_name)
        for warning in brain.corpus.warnings[:10]:
            log.warning("demo-data: %s", warning)
        yield
        for task in list(brain.tasks):
            task.cancel()

    app = FastAPI(title="Company Brain agent", version="0.1.0", lifespan=lifespan)
    app.state.brain = brain
    app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.time()
        response = await call_next(request)
        if request.url.path != "/events/stream":
            log.info("%s %s -> %s in %dms", request.method, request.url.path, response.status_code, (time.time() - started) * 1000)
        return response

    def get_brain() -> Brain:
        return app.state.brain

    @app.get("/health")
    async def health():
        brain = get_brain()
        return {
            "ok": True,
            "retriever": brain.retriever.name,
            "docs": len(brain.corpus.docs),
            "chunks": len(brain.corpus.chunks),
            "vectors": brain.index.vectors_ready,
            "llm": settings.llm_name,
            "people": len(brain.corpus.people),
            "uptime_s": int(time.time() - brain.started),
            "warnings": brain.corpus.warnings[:10],
        }

    @app.post("/ask", response_model=AskResponse)
    async def ask(body: AskRequest, request: Request):
        client = request.client.host if request.client else "anon"
        if not app.state.limiter.allow(client):
            raise HTTPException(status_code=429, detail="Too many questions. Try again in a minute.")
        try:
            return await get_brain().answerer.ask(body.question.strip())
        except Exception as exc:  # never let the demo show a stack trace
            log.exception("ask failed")
            raise HTTPException(status_code=500, detail=f"The agent failed: {exc}") from exc

    # ---------- events ----------

    @app.get("/events")
    async def list_events():
        return {"events": [e.model_dump() for e in get_brain().events.recent()]}

    @app.get("/events/stream")
    async def stream_events():
        return StreamingResponse(
            get_brain().events.stream(),
            media_type="text/event-stream",
            headers={"cache-control": "no-cache", "x-accel-buffering": "no", "connection": "keep-alive"},
        )

    @app.post("/events")
    async def post_event(body: EventIn):
        brain = get_brain()
        events = event_from_webhook(body.type, body.payload)
        for event in events:
            brain.events.emit(event)
        return events[0].model_dump() if len(events) == 1 else {"events": [e.model_dump() for e in events]}

    @app.delete("/events")
    async def clear_events():
        get_brain().events.clear()
        return {"ok": True}

    # ---------- roster ----------

    @app.get("/roster")
    async def roster():
        return {"people": [p.model_dump() for p in get_brain().roster.people]}

    @app.post("/roster/reset")
    async def roster_reset():
        brain = get_brain()
        brain.roster.reload()
        brain.events.clear()
        return {"people": [p.model_dump() for p in brain.roster.people]}

    @app.post("/roster/{handle}/status")
    async def roster_status(handle: str, body: StatusIn):
        brain = get_brain()
        person = brain.roster.find(handle)
        if not person:
            raise HTTPException(status_code=404, detail=f"No one called {handle} on the roster.")
        person = brain.roster.set_status(person, body.status)
        emitted: list[Event] = []
        if body.status == "left":
            successors = brain.roster.successors(person)
            emitted.append(brain.events.emit(Event(
                type="employee_left",
                title=f"{person.name} left {brain.corpus.manifest.get('company', 'the company')}",
                body=f"{person.name} ({person.role or 'engineer'}, {person.team or 'engineering'}) is marked as left. "
                     f"Owned paths: {', '.join(brain.corpus.owned_paths(person)) or 'none in CODEOWNERS'}. "
                     f"Writing the handoff report now" + (f"; likely successors: {', '.join(successors)}." if successors else "."),
                person=person.name,
                sources=[Source(type="owner", url=settings.blob_url("demo-data/team-roster.csv"), author=person.name, date=person.left, title="team-roster.csv")],
                severity="warn",
            )))

            async def write_report():
                brain.events.emit(await brain.roster.handoff_report(person))

            brain.spawn(write_report())
        elif body.status == "new":
            emitted.append(brain.events.emit(Event(
                type="new_hire",
                title=f"{person.name} joined as {person.role or 'engineer'}",
                body=f"Welcome {person.name} to {person.team or 'engineering'}. Drafting an onboarding plan.",
                person=person.name,
                severity="good",
            )))

            async def write_plan():
                brain.events.emit(await brain.roster.onboarding_plan(person))

            brain.spawn(write_plan())
        else:
            emitted.append(brain.events.emit(Event(type="info", title=f"{person.name} is active again", person=person.name)))
        return {"person": person.model_dump(), "events": [e.model_dump() for e in emitted]}

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        log.exception("unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "The agent hit an error."})

    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("brain.app:app", host="0.0.0.0", port=default_settings.port, reload=False)
