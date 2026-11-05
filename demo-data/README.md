# demo-data: the fake company "Acme"

Everything under this folder is made up. Acme, its employees, its customers, its incidents and
PayRail (its payment gateway) are invented as demo content for the Company Brain hackathon project.

Two sets of Acme material live here side by side:

- **Company Brain corpus** (the agent indexes this): Acme Shop, a six-engineer e-commerce backend with
  five recorded decisions, each backed by a PR, a Slack thread, a meeting note or ADR, and a current owner.
- **Service stubs and docs** (payments, auth, notifications): the PayRail-backed invoicing services with
  their own tests, plus the Slack, meeting and handoff documents written for them.

## Company Brain corpus

| Path | What it is |
|---|---|
| `team-roster.csv` | The roster the agent reads (`name,handle,email,role,team,status,started,left,manager`). 7 people. Alex Chen is the live-demo offboarding; Sam Patel is the new hire asking questions. |
| `acme/` | The code. Small real Python files whose docstrings point at the ADR/PR behind them, plus `CODEOWNERS` and `config/feature_flags.json`. |
| `docs/slack/` | Six Slack threads, one message per line: `**Name** (HH:MM): text`. |
| `docs/meetings/` | Four meeting notes, each with a `## Decisions` section. |
| `docs/adr/` | ADRs 0001-0005. |
| `docs/handoffs/` | Tomas's checkout handover and Alex's offboarding handoff ("three things nobody else knows"). |
| `prs/` | PR bodies. `bump-image-cache-ttl` deliberately has no "Why" (triggers the `pr_missing_why` event). |
| `issues/` | Three issue bodies. |
| `manifest.json` | People, repo, and the PR/issue number map. `number`/`url` are null until seeded. |
| `scripts/seed_github.sh` | Creates the PRs and issues on GitHub and writes their numbers to the manifest. |

Every doc has YAML front matter (`type, title, author, date, url, participants, pr`). Docs refer to PRs as
`{{pr:slug}}`; the indexer renders that to `PR #n` plus the url from the manifest.

### The five decisions

1. Payments go through a retry queue: 212 double charges in Nov 2025. Maya built it, Tomas argued for it, Priya owns it.
2. Checkout owner is Priya since 2026-03-02, after Tomas left. Handover notes exist.
3. We run our own image server: hosted was 4x the cost (June 2024). Alex owns it. Revisit if traffic doubles.
4. Search is Postgres full text, not Elasticsearch: "one less cluster to run" (Alex, April 2025).
5. Feature flags are a JSON file in the repo, not LaunchDarkly (Jordan, Feb 2025).

### Seeding real PRs and issues on GitHub

```
DRY_RUN=1 demo-data/scripts/seed_github.sh   # preview
demo-data/scripts/seed_github.sh             # creates branches, PRs, issues; writes numbers to manifest.json
```
Idempotent: existing titles are skipped. Then re-run the agent indexer so links point at real PR numbers.

## Service stubs (payments, auth, notifications)

| Path | What it is |
|---|---|
| `payments-service/` | Charges invoices through PayRail, tracks status, notifies merchants |
| `auth/` | Login, access tokens, sessions |
| `notifications/` | Customer email receipts |
| `frontend/` | Stub of the invoicing web app |
| `team-roster-services.csv` | Service ownership roster (`name,role,service_owned,joined_date,status`). Separate from the Company Brain `team-roster.csv`, which the agent parses with its own schema. |
| `docs/` | Slack threads, meeting notes, onboarding guide and handoff documents for upload to Onyx |

### Run the service tests

```
cd payments-service   # or auth, notifications
pip install -r requirements.txt
pytest

cd frontend
npm test
```
