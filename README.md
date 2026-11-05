# Company Brain

An agent that holds the whole company's memory. A new hire asks "why is X built this way?" and gets, in
seconds: who wrote it, why that decision was made, where it was discussed, and who owns it now, with links
to the pull request and the thread. We answer **why**, not just what.

Built at a hackathon on Nov 4, 2026 by a team of three (agent, data, frontend).

```
  new hire ──question──▶ frontend (/app) ──▶ agent /ask ──▶ retrieval over code + PRs + Slack + ADRs
                                                  │                 (Chroma, or Onyx when running)
                                                  └──▶ LLM writes a 2-sentence answer that cites sources
  Triggerware ──roster / GitHub triggers──▶ agent /events ──▶ handoff report, onboarding plan, "no why" flag
                                                  └──SSE──▶ frontend live events rail
```

## Quick start

```
make setup            # uv sync + npm install + .env.local
make dev              # agent :8000, frontend :3000, trigger bridge
```

Then open http://localhost:3000/app and ask "Why do payments go through a retry queue?".
For the wow moment open http://localhost:3000/team and mark Alex Chen as left: the handoff report appears
in the live events rail a few seconds later.

LLM keys are optional. Put `OPENROUTER_API_KEY` (or `ANTHROPIC_API_KEY`) in `agent/.env`; without a key the
agent answers in extractive mode from the same sources, so the demo never dies.

## Folders

| folder | what |
|---|---|
| `frontend/` | Next.js 16: landing, chat with source cards, live events rail, team page |
| `agent/` | FastAPI: `/ask`, `/events`, `/roster`; Chroma + sentence-transformers RAG; OpenRouter or Anthropic |
| `demo-data/` | the fake company Acme: code, PR bodies, Slack threads, meeting notes, ADRs, handoffs, roster |
| `triggerware/` | trigger definitions, the Triggerware↔agent bridge, a demo simulator |

`AGENTS.md` is the contract every folder follows.

## Roadmap (not in the demo)

Onboarding plans per role, offboarding knowledge capture before the person leaves, Slack and Notion
connectors on real workspaces, answer feedback that re-ranks sources.
