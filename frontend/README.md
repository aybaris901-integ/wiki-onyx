# Company Brain frontend

Next.js 16, no sign-in. The landing page is at `/`, the chat at `/app`, the demo control room at `/team`.

## Run it

```
npm install
npm run dev
```

Without any settings it runs on stand-in data, and everything on screen is stamped "Sample".

## Connect the real agent

Put the agent's base address in `.env.local` and restart the dev server:

```
ASK_BACKEND_URL=http://localhost:8000
```

The browser only talks to this app's `/api/*` routes, which forward to the agent on the server, so the
agent doesn't need CORS. See `/AGENTS.md` at the repo root for the full agent API.

| Page route | Agent route | What it is |
|---|---|---|
| `POST /api/ask` | `POST /ask` | A question in, an answer with sources out |
| `GET /api/events/stream` | `GET /events/stream` | Server-Sent Events, one event per `data:` line |
| `GET /api/events` | `GET /events` | The latest 50 events, newest first (the page polls this if the stream drops) |
| `POST /api/events` | `POST /events` | A Triggerware-style webhook in |
| `GET /api/roster` | `GET /roster` | The team roster |
| `POST /api/roster/[handle]/status` | `POST /roster/{handle}/status` | `{ "status": "left" \| "active" \| "new" }` |
| `POST /api/roster/reset` | `POST /roster/reset` | Reload the roster, clear events |

## What the chat sends and expects

`POST /ask` with `{ "question": "..." }`, back:

```json
{
  "answer": "One to three plain sentences.",
  "sources": [{ "type": "pr", "url": "https://github.com/org/repo/pull/482", "author": "Maya Okafor", "date": "2025-11-19" }],
  "meta": { "retriever": "chroma", "model": "...", "ms": 1234, "live": true }
}
```

`type` picks the card:

| type | Card label | Card color |
|---|---|---|
| `slack` | Discussed in | green |
| `pr` | Written in | blue |
| `commit` | Changed in | blue |
| `code` | Lives in (a link's last part shows as the file name) | black |
| `doc`, `adr`, `meeting`, `handoff` | Written down in | light blue |
| `owner` | Owned by (`author` is the owner) | red |

Optional on any source: `title` and `quote` (the exact line that backs the answer). Empty `sources` tells the
reader to check with a person. Return 429 when rate limited; the page waits 30 seconds.

## Live events

The `/app` page shows a "Live events" rail (a button and bottom sheet on phones). Each event is a card with
its type, time, person, a severity tone (warn red, good green, info blue), an expandable markdown body and
compact source cards. Handoff reports and onboarding plans open expanded.

## Team page

`/team` lists the roster. "Mark as left" (confirm with a second click) posts the status change; the agent then
emits `employee_left` and, a few seconds later, `handoff_report`. "Onboarding plan" does the same for new hires.
"Reset demo" puts everything back. In sample mode the same flow runs against an in-memory roster, so the demo
works with no agent at all.

## Demo questions

Edit `EXAMPLE_QUESTIONS` in `lib/answer.ts`. Sample answers live in `lib/mock.ts`.
