# Architecture meeting notes, 2026

---

## Architecture meeting: 2026-02-05

**Attendees:** Alex Chen (acting tech lead), Sam Patel, Maria Lopez, Priya Shah
**Notes by:** Maria Lopez
**Context:** The engineering manager role has been vacant since November 2025. Until it's filled, Alex is acting as tech lead and these meetings are how we make cross-team decisions.

### Topic 1: Polling PayRail for payment status

The 2026-01-30 month-end run had about 2,400 open payments. Polling each one every 30 seconds comes to 4,800 requests a minute against PayRail's limit of 3,000. 38% of polls got a 429, and p95 status lag reached about 11 minutes, up from about 40 seconds.

Options discussed:

| Option | View |
|---|---|
| Adaptive polling | Delays the problem, and worsens lag for backed-off payments |
| Paid PayRail tier with a higher limit | Pays to keep a design that gets worse with volume |
| PayRail SSE stream | Beta, no delivery guarantee |
| Webhooks plus a slow reconcile job | Preferred |

**Decision:** Move to signed webhooks and keep an hourly reconcile job for payments pending more than an hour. Decided by Alex, no objections. Alex to implement (PR #1).

### Topic 2: Session lookup latency

Session lookup p99 is 180 ms at peak against a 20 ms target. The `sessions` table has about 31 million rows. Auth shares a Postgres cluster with payments, so session load affects charges.

Sam proposed moving sessions to Redis. Maria asked for tuned Postgres to be considered first. Priya asked whether users would notice the migration.

**Decision:** Move sessions to Redis if a staging benchmark confirms the gain. Sam to run the benchmark and implement (PR #2). Maria, as auth owner, to review. Everyone accepts one forced login at cutover.

**Principle agreed (Alex's wording):** "Redis is for data we can afford to lose." Sessions qualify, because the worst case is logging in again. Anything to do with money doesn't.

### Topic 3: Knowledge concentration (raised by Priya)

Priya pointed out that most questions about payments end in "ask Alex". Alex agreed that a lot of PayRail behaviour is only in Alex's head, and said it'd get written down "when things calm down".

**Decision:** None. No action item was recorded.

### Action items

| Owner | Item | Status at time of writing |
|---|---|---|
| Alex | Webhooks PR | Open |
| Sam | Redis benchmark and PR | Open |
| Maria | Warn support about the forced login | Open |

---

## Architecture meeting: 2026-08-20

**Attendees:** Tom Becker (supervisor, started 2026-08-03), Alex Chen, Maria Lopez, Sam Patel, Priya Shah
**Notes by:** Priya Shah
**Context:** Alex gave notice on 2026-08-07, and the last day is 2026-09-04. This meeting was called to decide who takes what, and what has to happen first.

### Topic 1: Who takes over payments-service

Maria takes over payments-service. Shadowing started on 2026-08-17, and Maria becomes the formal owner on 2026-09-07. Maria keeps auth and notifications because there's nobody else to give them to.

Sam said this puts three services on one person. Tom said that opening a backend hire would be raised with leadership but that there was no timeline.

**Decision:** Maria owns payments-service from 2026-09-07. Decided by Tom. Sam becomes secondary on-call for payments.

### Topic 2: The ACH guard from PR #8

Tom asked again whether the ACH batch window logic could be simplified, since it fires rarely. Alex explained that it fires rarely because the window is 30 minutes long, and that without it customers get dunning emails for invoices they've paid.

Alex also explained, for the first time to most of the room, that the code doesn't handle month end. The settlement file can be 4 to 6 hours late at month and quarter end, and Alex has been correcting this by hand with a script on Alex's laptop on the first business day of each month.

Maria asked how long a proper fix would take. Alex's estimate: 3 to 4 weeks to make the settlement file the source of truth for ACH. Too long to do before leaving.

**Decisions:**

- Don't delete or simplify `ach_guard.py`.
- A proper fix isn't going to happen before Alex leaves. Tom to decide on priority later.
- Alex to commit `recon_ach.py` and write up how it works.
- Alex and Maria to run the 2026-09-01 reconciliation together.

### Topic 3: Should we make Kafka the standard queue, now the service count is growing? (raised by Tom)

Tom asked whether we should standardise on a message broker, having used one at a previous company. Sam and Alex both said no. The volumes (about 60k webhook deliveries and 400 emails a day) are comfortably handled by Postgres tables and workers, and a broker would be one more system to run with one fewer backend engineer on the team. See PR #3 and PR #7.

**Decision:** No broker. Look again if webhook deliveries approach 1 million a day.

### Topic 4: Things Alex is worried about

Alex listed these. Full detail is in the handoff document.

- Month-end ACH reconciliation (above).
- Stuck `in_progress` idempotency keys have no automated cleanup.
- PayRail's support relationship has been run personally by Alex.

### Action items

| Owner | Item | Due | What happened |
|---|---|---|---|
| Alex | Write handoff document | 2026-09-03 | Done |
| Alex | Commit `recon_ach.py` | 2026-09-01 | **Not done.** Alex ran out of time |
| Alex + Maria | Run the 2026-09-01 reconciliation together | 2026-09-01 | **Not done together.** Maria was pulled onto an auth problem and Alex ran it alone |
| Tom | Raise backend hire with leadership | 2026-09-15 | Raised, no timeline |
| Tom | Decide priority of the ACH settlement file project | Not set | **Still open** |
