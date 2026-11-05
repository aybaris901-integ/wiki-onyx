# Company Brain — repo contract

Hackathon build (Nov 4, 2026). One flow done perfectly: a new hire asks "why is X built this way?"
and the agent answers in seconds with WHO wrote it, WHY, WHERE it was discussed, WHO owns it now,
with links. Plus a live "events" feed (Triggerware-style triggers) and the demo wow moment:
mark Alex as "left" → a handoff report appears automatically.

Repo on GitHub: https://github.com/aybaris901-integ/wiki-onyx  (branch: company-brain)

## Layout

- `frontend/`   Next.js 16 app. Landing at `/`, chat at `/app`. Talks only to its own `/api/*` routes,
                which proxy to the agent (`ASK_BACKEND_URL`, default http://localhost:8000).
- `agent/`      Python 3.14 FastAPI service (uv). RAG over `demo-data/` with Chroma + sentence-transformers,
                optional Onyx retriever, LLM via OpenRouter or Anthropic, extractive fallback with no key.
- `demo-data/`  The fake company "Acme" (team name: Acme Shop). Everything the agent indexes.
- `triggerware/` Trigger definitions + a simulator that posts events to the agent.

## demo-data layout

```
demo-data/
  manifest.json              # people, repos, PR number map (see below)
  team-roster.csv            # name,handle,email,role,team,status,started,left,manager
  acme/                      # the fake company's code (small real files; the agent git-blames these)
    services/payments/...
    services/checkout/...
    services/images/...
    CODEOWNERS
  docs/
    slack/<channel>-<YYYY-MM-DD>-<slug>.md     # Slack threads, see format
    meetings/<YYYY-MM-DD>-<slug>.md             # meeting notes with "Decisions" section
    adr/<NNNN>-<slug>.md                        # architecture decision records
    handoffs/alex-offboarding.md                # Alex's offboarding handoff doc
  prs/<slug>.md                                 # PR bodies (title, author, date, branch, body with "Why")
  scripts/seed_github.sh                        # creates real PRs/issues on the repo via gh, writes numbers to manifest
```

Every doc starts with YAML front matter:

```
---
type: slack | meeting | adr | handoff | pr | issue
title: ...
author: Maya Okafor            # display name from team-roster.csv
date: 2025-11-17
channel: #payments             # slack only
participants: [Maya Okafor, Tomas Ruiz]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/payments-2025-11-17-retry-queue.md
pr: retry-queue                # optional: slug of the PR this relates to
---
```

Slack thread body: one line per message, `**Name** (HH:MM): text`.

`manifest.json`:
```
{
  "company": "Acme",
  "repo": "aybaris901-integ/wiki-onyx",
  "branch": "company-brain",
  "people": { "Maya Okafor": { "handle": "maya", "role": "...", "team": "...", "status": "active" } },
  "prs": { "retry-queue": { "number": null, "url": null, "title": "...", "author": "Maya Okafor", "date": "2025-11-19", "files": ["demo-data/acme/services/payments/retry_queue.py"] } }
}
```
Docs reference PRs as `{{pr:retry-queue}}`; the indexer renders that to `PR #482` + url from the manifest, or a
GitHub search url if `number` is null.

### The story (all agents use the same facts)

People (team-roster.csv):
- Maya Okafor — Senior Backend Engineer, Payments. Active.
- Tomas Ruiz — Staff Engineer, Checkout. Left 2026-03-01 (wrote most of checkout).
- Priya Raman — Backend Engineer, Checkout → now owns checkout + payments retry queue.
- Dana Whitlock — Infra Lead, Platform. Active.
- Alex Chen — Senior Engineer, Images/Media + search. Active (THE DEMO: we mark Alex "left" live).
- Jordan Lee — Engineering Manager. Active.
- Sam Patel — new hire (joined 2026-11-02), Backend. The person asking questions.

Decisions (each has: a PR, a Slack thread, a meeting or ADR, and an owner):
1. Payments go through a retry queue (not inline) — Nov 2025 sale double-charged 212 orders when the
   provider timed out. Maya built it (PR retry-queue, 2025-11-19); Tomas argued for the queue in #payments
   2025-11-17; Priya owns it now (CODEOWNERS 2026-03-02).
2. Checkout owner is Priya since 2026-03-02, after Tomas left; Tomas's handover notes exist (docs/handoffs/tomas-checkout-handover.md).
3. We run our own image server — Dana priced a hosted CDN in June 2024: 4x the cost at our catalog size;
   revisit if traffic doubles (ADR 0003, #infra thread 2024-06-20, commit by Dana 2024-06-24). Alex Chen owns
   image pipeline + the search indexer.
4. Search uses Postgres full-text, not Elasticsearch — Alex Chen, ADR 0005 (2025-04), "one less cluster to run".
5. Feature flags are a JSON file in the repo, not LaunchDarkly — Jordan, meeting 2025-02-10, cost + 6 engineers.

Alex's offboarding handoff (docs/handoffs/alex-offboarding.md) must list: owned systems (image server,
search indexer, thumbnail cron), open risks, who should take over (Dana for images, Priya for search),
runbooks, and 3 things nobody else knows.

## Agent HTTP API (FastAPI, port 8000)

`POST /ask`  body `{ "question": "..." }` →
```
{
  "answer": "One to three plain sentences. Names the who, why, where, and current owner.",
  "sources": [
    { "type": "pr" | "slack" | "commit" | "code" | "doc" | "owner",
      "url": "https://...", "author": "Maya Okafor", "date": "2025-11-19",
      "title": "optional", "quote": "optional exact line that backs the answer" }
  ],
  "meta": { "retriever": "chroma" | "onyx", "model": "...", "ms": 1234, "live": true }
}
```
Return 429 when rate limited; 5xx on failure. The frontend waits 30 s.

`GET /health` → `{ "ok": true, "retriever": "chroma", "docs": 42, "llm": "openrouter/..." | "extractive" }`

Events (Triggerware-style):
- `GET /events/stream`  Server-Sent Events. Each `data:` is one Event JSON.
- `GET /events`          `{ "events": [Event, ...] }` most recent first (max 50).
- `POST /events`         webhook in. Body: `{ "type": "...", "payload": {...} }`. Returns the stored Event.

Event JSON:
```
{ "id": "evt_...", "type": "employee_left" | "handoff_report" | "new_hire" | "onboarding_plan" |
         "pr_merged" | "pr_missing_why" | "info",
  "title": "Alex Chen left Acme", "body": "markdown", "at": "2026-11-04T19:20:00Z",
  "person": "Alex Chen", "sources": [Source, ...], "severity": "info" | "warn" | "good" }
```

Roster:
- `GET /roster` → `{ "people": [ {name, handle, role, team, status, started, left, manager} ] }`
- `POST /roster/{handle}/status` body `{ "status": "left" | "active" | "new" }` → updates roster in memory
  (and team-roster.csv), emits `employee_left` (or `new_hire`), then generates and emits `handoff_report`
  (or `onboarding_plan`) using the LLM over that person's PRs/docs/code. Returns `{ "person": ..., "events": [...] }`.
- `POST /roster/reset` → reloads team-roster.csv from disk, clears events.

PR checks: `POST /events` with `type: "pr_merged"` and payload `{ number, title, body, author, url }` → the
agent checks the body for a why (words like because/why/context/so that, or a "## Why" heading) and emits
`pr_missing_why` when absent.

Config (env): `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` (default `anthropic/claude-sonnet-4.5`),
`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (default `claude-sonnet-4-5`), `ONYX_URL`, `ONYX_API_KEY`,
`DEMO_DATA_DIR` (default `../demo-data`), `REPO_SLUG`, `REPO_BRANCH`, `PORT`.
With no LLM key the agent still answers: extractive mode (top chunks → templated answer) so the demo never dies.

## Frontend ↔ agent

- `POST /api/ask` → agent `/ask` (exists).
- `GET /api/events/stream` → proxies SSE from agent. `GET /api/events` → list.
- `GET /api/roster`, `POST /api/roster/[handle]/status`, `POST /api/roster/reset`.
- Without `ASK_BACKEND_URL` everything falls back to samples stamped "Sample" on screen.

## Run

```
# agent
cd agent && uv sync && uv run python -m brain.index && uv run uvicorn brain.app:app --port 8000
# frontend
cd frontend && npm install && echo ASK_BACKEND_URL=http://localhost:8000 > .env.local && npm run dev
```
`make dev` at the root runs both.

## Rules

- Python via uv only. Tests with `uv run pytest -n auto`.
- No AI attribution in commits.
- Links must open real pages: GitHub blob/PR urls on this repo, never example.com, in demo data.
