# Triggerware integration

Triggerware watches the company's data and fires triggers; the Company Brain agent turns each trigger
into something useful: a handoff report when someone leaves, an onboarding plan when someone joins, a
flag when a PR is merged with no "why".

## Triggers (triggers.yaml)

| trigger | watches | agent reaction |
|---|---|---|
| `employee_left` | `team-roster.csv` status → `left` | writes a handoff report from that person's PRs, threads, code and handoff doc |
| `new_hire` | `team-roster.csv` status `new` | writes a week-by-week onboarding plan |
| `pr_merged` | GitHub connector, merged PRs | flags the PR when the body has no why |

## Run

```
# with Triggerware (Mac/Windows)
curl -fsSL tw2-releases.s3.us-east-2.amazonaws.com/install.sh | sh
triggerware start
uv run --with triggerware triggerware/bridge.py

# without it: same bridge, local file watcher + gh polling
uv run triggerware/bridge.py
```

The bridge posts to the agent at `AGENT_URL` (default `http://localhost:8008`).

## Demo

```
uv run triggerware/simulate.py alex-left     # or click "Mark as left" on /team
uv run triggerware/simulate.py pr-no-why
```
