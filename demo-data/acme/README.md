# Acme Shop

The backend for Acme's online shop. Four services, one Postgres, no Kubernetes.

| Service | What it does | Owner | Why it is built this way |
|---|---|---|---|
| `services/payments` | Charges customers through a retry queue | @priya | [ADR 0001](../docs/adr/0001-payments-retry-queue.md): inline retries double charged 212 orders in Nov 2025 |
| `services/checkout` | Carts and orders | @priya | [ADR 0004](../docs/adr/0004-checkout-ownership.md): Priya took over when Tomas left, March 2026 |
| `services/images` | Our own image server and thumbnail cron | @alex | [ADR 0003](../docs/adr/0003-self-hosted-image-server.md): hosted CDN was 4x the cost at our catalog size |
| `services/search` | Postgres full-text search, no Elasticsearch | @alex | [ADR 0005](../docs/adr/0005-postgres-full-text-search.md): one less cluster to run |
| `config/feature_flags.json` | Feature flags, in the repo | @jordan | [ADR 0002](../docs/adr/0002-feature-flags-in-repo.md): six engineers do not need LaunchDarkly |

Decisions live in `docs/adr/`. Discussions live in Slack (exported to `docs/slack/`). Meeting notes in `docs/meetings/`.
If you are new: ask the Company Brain before you ask a person.
