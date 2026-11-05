# demo-data: the fake company "Acme"

Everything the Company Brain indexes. Acme Shop is a six-engineer e-commerce backend with five
recorded decisions, each backed by a PR, a Slack thread, a meeting note or ADR, and a current owner.

| Folder | What |
|---|---|
| `team-roster.csv` | 7 people. Alex Chen is the live-demo offboarding; Sam Patel is the new hire asking questions. |
| `acme/` | The code. Small real Python files whose docstrings point at the ADR/PR behind them, plus `CODEOWNERS` and `config/feature_flags.json`. |
| `docs/slack/` | Six Slack threads, one message per line: `**Name** (HH:MM): text`. |
| `docs/meetings/` | Four meeting notes, each with a `## Decisions` section. |
| `docs/adr/` | ADRs 0001-0005. |
| `docs/handoffs/` | Tomas's checkout handover and Alex's offboarding handoff ("three things nobody else knows"). |
| `prs/` | PR bodies. `bump-image-cache-ttl` deliberately has no "Why" (triggers the `pr_missing_why` event). |
| `issues/` | Three issue bodies. |
| `manifest.json` | People, repo, and the PR/issue number map. `number`/`url` are null until seeded. |

Every doc has YAML front matter (`type, title, author, date, url, participants, pr`). Docs refer to PRs as
`{{pr:slug}}`; the indexer renders that to `PR #n` plus the url from the manifest.

## The five decisions

1. Payments go through a retry queue: 212 double charges in Nov 2025. Maya built it, Tomas argued for it, Priya owns it.
2. Checkout owner is Priya since 2026-03-02, after Tomas left. Handover notes exist.
3. We run our own image server: hosted was 4x the cost (June 2024). Alex owns it. Revisit if traffic doubles.
4. Search is Postgres full text, not Elasticsearch: "one less cluster to run" (Alex, April 2025).
5. Feature flags are a JSON file in the repo, not LaunchDarkly (Jordan, Feb 2025).

## Seeding real PRs and issues on GitHub

```
DRY_RUN=1 demo-data/scripts/seed_github.sh   # preview
demo-data/scripts/seed_github.sh             # creates branches, PRs, issues; writes numbers to manifest.json
```
Idempotent: existing titles are skipped. Then re-run the agent indexer so links point at real PR numbers.
