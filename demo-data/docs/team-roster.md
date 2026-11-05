# Acme engineering team roster

**Last updated:** 2026-11-02 by Tom Becker

## Current team

| Name | Role | Joined | Owns | Backup for |
|---|---|---|---|---|
| Tom Becker | Engineering supervisor | 2026-08-03 | Priorities, staffing | |
| Maria Lopez | Backend engineer | 2023-06-05 | payments-service, auth, notifications | |
| Sam Patel | Infrastructure / DevOps | 2022-01-10 | Infrastructure, Redis, Postgres, CI, on-call tooling | payments-service, auth, notifications |
| Priya Shah | Frontend lead | 2022-09-19 | Frontend | |

## Former team members

| Name | Role | Joined | Left | Owned | Now owned by |
|---|---|---|---|---|---|
| Alex Chen | Senior backend engineer, acting tech lead from November 2025 | 2021-03-15 | 2026-09-04 | payments-service | Maria Lopez, since 2026-09-07 |

## Service ownership

| Service | Owner | Backup | Previous owner | Notes |
|---|---|---|---|---|
| payments-service | Maria Lopez | Sam Patel | Alex Chen (until 2026-09-04) | Read `alex-offboarding-handoff.md` before changing it |
| auth | Maria Lopez | Sam Patel | | Sessions in Redis, 15 minute access tokens |
| notifications | Maria Lopez | Sam Patel | | Receipts through a Postgres outbox |
| frontend | Priya Shah | None | | |
| Infrastructure | Sam Patel | None | | |

## On-call

| Rotation | Primary | Secondary |
|---|---|---|
| Backend (payments, auth, notifications) | Maria Lopez | Sam Patel |
| Infrastructure | Sam Patel | Maria Lopez |

## Recurring manual jobs

| Job | When | Who |
|---|---|---|
| ACH reconciliation against PayRail's settlement file (issue #9) | First business day of each month | Maria Lopez |

## Open roles

Backend engineer: raised with leadership in September 2026. No timeline yet.
