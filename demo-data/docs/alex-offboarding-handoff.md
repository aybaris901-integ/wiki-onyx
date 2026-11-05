# Alex Chen offboarding handoff

**Written by:** Alex Chen
**Date:** 2026-09-03 (last day: 2026-09-04)
**Handing over to:** Maria Lopez (payments-service), with Sam Patel as secondary
**Addenda:** Maria Lopez, 2026-10-06 and 2026-11-03 (at the end of this document)

Maria, sorry this isn't more complete. I've tried to be honest about what's only in my head. Read "What isn't documented" first, because that's the part that will hurt.

## What I'm handing over

| Item | New owner | State |
|---|---|---|
| payments-service code and on-call | Maria (primary), Sam (secondary) | Stable, apart from the risks below |
| PayRail integration | Maria | See "What isn't documented" |
| Month-end ACH reconciliation | Maria | Manual, see Risk 1 |
| PayRail API key and webhook secret | Sam | In the team password vault. Sam has checked that both work |
| PayRail account manager relationship | Maria | I've introduced you by email. Most of my history with them is in phone calls |

The reasoning for the major decisions is in the PR descriptions, and I'd read them in this order: #1 webhooks, #3 retries, #4 idempotency, #8 ACH guard. If you're short on time, read #4 and #8.

## What isn't documented

**1. `recon_ach.py` isn't in the repo.** I said I'd commit it by 2026-09-01 and I didn't get to it. It's on my work laptop, which gets wiped when I hand it in tomorrow, and I've run out of time to make it fit to share. On the first business day of each month, it compares PayRail's settlement CSV to our records. I'm sorry, I know this is the big one. I'll try to send what I can remember.

**2. PayRail's batch window isn't in their docs.** The 23:50 to 00:20 UTC window, the second event queue and the stale `GET` behaviour are all things I worked out from production logs and confirmed in phone calls with their support. Nothing is in writing. If they change it, we won't be told, and the first sign will be wrong invoice states.

**3. The month-end delay is the same.** The 4 to 6 hour settlement file delay is what I've observed. PayRail has never committed to any timing.

**4. Some banks send ACH reversals with a different trace number from the original.** The script has a special case for it. I can't describe the matching rule accurately from memory, and I don't think it's written down anywhere.

**5. Secret rotation needs a phone call.** Rotating `PAYRAIL_WEBHOOK_SECRET` needs an overlap window, which PayRail arranges manually. Call before you rotate, or webhooks will start failing signature checks and you'll be relying on the hourly reconcile job.

**6. Replaying dead merchant webhooks is done by hand in SQL.** Set `status = 'queued'`, `attempts = 0`, `next_attempt_at = now` on the row in `webhook_deliveries`. There's no admin tool. Support asks whoever's on-call.

**7. Four merchants call the API directly** rather than going through our UI. I emailed all of them about the `Idempotency-Key` requirement in April. Maria did the follow-ups, so Maria knows the people.

**8. Finance runs retry batches weekly**, on Mondays. That's why idempotency keys are kept for 7 days rather than 24 hours. Don't shorten it without talking to finance.

## Known risks

| # | Risk | Severity | What to do |
|---|---|---|---|
| 1 | ACH invoices end up in the wrong state at month end or quarter end. A real return can look paid, and nothing alerts on it. Issue #9 | **High** | Reconcile by hand on the first business day of every month until the settlement file project happens |
| 2 | Idempotency keys stuck `in_progress` after a PayRail outage or crash. The customer is blocked until someone clears them. Issue #10, a follow-up to PR #4 | Medium | Clear by hand: check PayRail first and never delete a key blind |
| 3 | No retention on `webhook_deliveries` or `payrail_events`. Both tables keep growing. Sam asked for this in PR #3 and it wasn't built | Low for now | Add a cleanup job before it becomes an emergency |
| 4 | If notifications is down when payments calls it, the receipt isn't retried. See PR #7 | Low | Accepted for now |
| 5 | Payments, auth and notifications all now sit with one person. Maria shouldn't have to carry that | **High** | This one is Tom's to solve |

## Please don't

- **Delete or simplify `ach_guard.py`.** It looks like dead code most of the time. It isn't.
- **Shorten the 90 minute hold.** It's tied to when the settlement file comes out. See PR #8.
- **Move idempotency keys to Redis** because someone notices it would be faster. See PR #4.
- **Remove the hourly reconcile job** because webhooks seem reliable. It's the only thing that catches a lost event.

## Who owns what from 2026-09-07

| Area | Owner | Backup |
|---|---|---|
| payments-service | Maria Lopez | Sam Patel |
| auth | Maria Lopez | Sam Patel |
| notifications | Maria Lopez | Sam Patel |
| Infrastructure, Redis, on-call tooling | Sam Patel | None |
| Frontend | Priya Shah | None |
| Priority and staffing decisions | Tom Becker | |

## Contact

I'm happy to answer questions by email until 2026-10-31. After that I'm starting somewhere new and can't promise anything.

Good luck, and thank you.

Alex

---

## Addendum: Maria Lopez, 2026-10-06

We got caught by Risk 1 sooner than I'd hoped. Nobody ran reconciliation on 2026-10-01, because I hadn't taken in that it had to happen that day and it wasn't in any calendar. Three invoices were wrong after the September month end and quarter end: two customers got dunning emails for paid invoices, and a real return of **$18,940** showed as paid until a customer's account manager queried it on 2026-10-05. The money has since been recovered. Details are in issue #9.

I emailed Alex, who replied today with a description of the script from memory. It's quoted in issue #9. The trace number matching is the part Alex can't reconstruct.

I've added a recurring calendar entry for the first business day of each month.

## Addendum: Maria Lopez, 2026-11-03

I ran the 2026-11-02 reconciliation by hand in a spreadsheet. It took about half a day and found nothing, but I don't trust that fully because I can't handle the trace number case. Alex's email offer ended on 2026-10-31, so there's now nobody to ask. The next run is due on 2026-12-01.

Still waiting on a priority decision for the settlement file project (Tom) and the idempotency key cleanup job (issue #10).
