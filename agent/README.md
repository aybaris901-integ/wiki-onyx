# Company Brain agent

FastAPI service that answers "why is it built this way?" with sources, and runs the Triggerware-style
event feed (employee left → handoff report, new hire → onboarding plan, PR merged without a why → flag).

```
uv sync
uv run python -m brain.index          # optional: build the Chroma index up front
uv run uvicorn brain.app:app --port 8008
```

The server indexes `../demo-data` on startup. Keyword search answers immediately; the embedding index
(sentence-transformers `all-MiniLM-L6-v2`) builds in the background and joins in when ready.

With no API key the agent answers in **extractive mode** (quotes stitched from the top sources). Set
`OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` (see `.env.example`) for written answers. Set `ONYX_URL` to
retrieve through a self-hosted Onyx, with automatic fallback to the local index.

Try it:

```
curl -s localhost:8008/health
curl -s localhost:8008/ask -H 'content-type: application/json' -d '{"question":"Why do payments go through a queue?"}'
curl -N localhost:8008/events/stream &
curl -s -X POST localhost:8008/roster/alex/status -H 'content-type: application/json' -d '{"status":"left"}'
curl -s -X POST localhost:8008/events -H 'content-type: application/json' \
  -d '{"type":"pr_merged","payload":{"number":99,"title":"Bump image cache TTL","author":"Alex Chen","body":"Bump to 3600.","url":"https://github.com/aybaris901-integ/wiki-onyx/pull/99"}}'
```

Tests: `uv run pytest -n auto`. The contract (routes and JSON shapes) is in the repo's `AGENTS.md`.
