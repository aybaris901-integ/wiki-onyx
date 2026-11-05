# Slack threads: Acme engineering decisions, 2026

Exported from Acme's Slack. Times are UTC.

---

## Thread 1: Moving from PayRail polling to webhooks

**Channel:** #eng-payments
**Date:** 2026-02-02 to 2026-02-03
**People:** Alex Chen, Sam Patel, Maria Lopez, Priya Shah
**Outcome:** Move to webhooks, keep an hourly reconcile job. Confirmed at the 2026-02-05 architecture meeting, shipped in PR #1.

**Alex Chen** 2026-02-02 09:14
post-mortem-ish on friday's month end run. we had ~2400 open payments. polling each one every 30s is 4800 req/min and PayRail's limit is 3000. 38% of our polls got 429'd

**Alex Chen** 09:15
p95 status lag went from ~40s to ~11 min. that's why support got buried

**Priya Shah** 09:21
yeah I saw the tickets. "my invoice still says unpaid, should I pay again??" which is not a question I ever want a customer asking

**Sam Patel** 09:26
can't we just ask them for a higher limit?

**Alex Chen** 09:31
I did. it's a paid tier. and we'd have this conversation again at 5000 open payments. nearly all those requests return "still pending" anyway, we're paying to ask a question whose answer hasn't changed

**Maria Lopez** 09:40
PayRail has webhooks right? why did we poll in the first place

**Alex Chen** 09:44
because in 2023 we had 50 payments a day and polling took an afternoon to write. no great reason. they also have an SSE stream now but it's beta with no delivery guarantee, and I'm not building billing on a beta

**Sam Patel** 09:52
webhooks means a public endpoint. they don't publish IP ranges so I can't allowlist. signature check is all we've got

**Alex Chen** 09:55
HMAC with a timestamp, so replays are out too. should be fine

**Maria Lopez** 10:03
and if a webhook just never arrives? I'd hate to have an invoice stuck pending forever because PayRail dropped one

**Alex Chen** 10:06
keep a job that only looks at payments pending > 1h. hourly. normally a handful of calls instead of 4800 a minute. best of both

**Sam Patel** 2026-02-03 08:30
works for me. put it behind the existing ingress please

**Alex Chen** 08:41
will bring it to thursday's arch meeting but I think this is decided unless someone objects

---

## Thread 2: Session latency and the move to Redis

**Channel:** #infra
**Date:** 2026-02-12 to 2026-02-13
**People:** Sam Patel, Maria Lopez, Alex Chen
**Outcome:** Benchmark confirmed the Redis plan from the 2026-02-05 meeting. Shipped in PR #2, cut over on 2026-03-01.

**Sam Patel** 2026-02-12 14:02
session lookup p99 hit 180ms again this morning during the 8am peak. target's 20. sessions table is at 31M rows, autovacuum can't keep up

**Maria Lopez** 14:08
that's on me as auth owner, the nightly cleanup is not doing enough. could partition by day? I can look

**Sam Patel** 14:15
partitioning helps with bloat but not the other thing, which is we're on the same cluster as payments. session traffic is eating connections that charges need

**Alex Chen** 14:19
yeah I've seen payment calls queue up for a connection at 8am. I'd assumed it was us

**Sam Patel** 14:27
I'll have numbers tomorrow. benchmarking redis with prod-sized load in staging

**Sam Patel** 2026-02-13 11:40
staging, same load. postgres p99 165ms, redis p99 2.1ms. I estimate tuned postgres gets maybe 40ms at best

**Maria Lopez** 11:46
not much of a contest. what about a local in-process cache instead? no new infra

**Sam Patel** 11:49
logout wouldn't take effect until every instance's cache expired. security would hate it

**Maria Lopez** 11:51
fair. and what do we lose if redis dies?

**Sam Patel** 11:55
sentinel failover, up to about a second of writes with AOF everysec. worst case some people log in again

**Alex Chen** 12:03
ok for sessions. but please everyone remember why it's ok: the worst case is a login. it doesn't make redis a good place for anything else. the test is "can we afford to lose this"

**Sam Patel** 12:05
agreed. this isn't "redis is faster so use it everywhere"

**Maria Lopez** 12:10
I'd rather not write a dual-write migration to save one login. hard cutover on a sunday?

**Sam Patel** 12:12
sunday march 1. I'll warn support on the friday before

---

## Thread 3: Kestrel Freight outage and webhook retries

**Channel:** #eng-payments
**Date:** 2026-03-05 to 2026-03-06
**People:** Alex Chen, Sam Patel, Maria Lopez
**Outcome:** Replace fixed-interval inline retries with a queue, exponential backoff and full jitter. Shipped in PR #3.

**Maria Lopez** 2026-03-05 16:31
Kestrel Freight's account manager is asking why we're "attacking their ERP". their endpoint was down for 47 min and when it came back we hit it with about 12k deliveries

**Alex Chen** 16:35
oh no. yeah. every failed delivery retries at 60s, so they all stay in lockstep

**Sam Patel** 16:38
FYI they've blocked our egress IP

**Alex Chen** 16:44
also just noticed status updates for everyone else were lagging 9 min during this. the retry sleeps inline in the worker so a slow merchant blocks everybody. that's the part that really worries me

**Maria Lopez** 16:52
and whatever failed past 5 tries is just gone? Kestrel asked for a replay and I had nothing to give them

**Alex Chen** 16:55
gone. they'll have to reconcile from a CSV. I'll own that apology

**Alex Chen** 2026-03-06 10:12
proposal: queue deliveries in a table, worker sends them, exponential backoff. and it needs full jitter, because plain backoff keeps them in sync and they'd still all come back together

**Sam Patel** 10:20
do you want SQS for this? I could stand it up

**Alex Chen** 10:24
do we need it? it's 60k deliveries a day. a table and a worker does that fine and support can query it

**Sam Patel** 10:29
honestly no, I'd rather not run another thing. table's fine until maybe 1M/day. just index it properly

**Maria Lopez** 10:33
someone will suggest buying one of those webhook delivery products

**Alex Chen** 10:35
payment data through another vendor, another security review, and a monthly bill. not for this

**Maria Lopez** 10:41
ok. and please respect Retry-After, a couple of big merchants send it

**Alex Chen** 10:42
yep. 10 attempts, up to about 8.5 hours. and we keep dead ones so support can replay them

---

## Thread 4: The double-charge incident, and why keys are not in Redis

**Channel:** #incidents
**Date:** 2026-04-14 to 2026-04-15
**People:** Alex Chen, Maria Lopez, Sam Patel, Priya Shah
**Outcome:** INC-2026-007. Idempotency keys go in Postgres (PR #4), with client changes in PR #5.

**Maria Lopez** 2026-04-14 14:19
support says Northwind Logistics was charged twice for one invoice. $48,200. anyone else seeing this?

**Alex Chen** 14:21
looking

**Sam Patel** 14:23
PayRail latency is through the roof. p50 over 10s. our client timeout is 10s

**Alex Chen** 14:31
it's bad. a timeout doesn't mean it failed. PayRail is still processing them after we give up, then we retry and that's a new charge. they have no way to know it's the same payment. I'm seeing dozens

**Priya Shah** 14:34
frontend also retries on 5xx 😬 and the button's still enabled so people are clicking again

**Alex Chen** 14:36
turning off charging for now. Sam can you flip the flag

**Sam Patel** 14:37
done

**Alex Chen** 14:52
last duplicates were around now. PayRail is recovering

**Maria Lopez** 17:40
final count from the PayRail export: 37 invoices across 9 merchants, $212,480 charged twice. finance is starting refunds. the ACH ones take days

**Alex Chen** 2026-04-15 09:05
we need idempotency keys on charging, client generated, passed through to PayRail. should've had them from day one and that's on me

**Sam Patel** 09:11
just use redis SET NX? it's already there and you could ship today

**Alex Chen** 09:20
no. redis loses up to a second of writes on failover and can evict under memory pressure. lose a key and you've got a double charge. think about when that would happen, too: PayRail's having a bad day, everyone's retrying

**Alex Chen** 09:21
this is the same test as sessions. we can afford to lose a session. we can't afford to lose this

**Sam Patel** 09:27
yeah ok, I withdraw that. postgres then. primary key as the lock

**Alex Chen** 09:28
adds ~2ms to a call that takes 800ms at PayRail anyway. speed isn't the issue

**Maria Lopez** 09:34
why not a unique constraint on invoice_id? even simpler

**Alex Chen** 09:37
blocks a legit retry after a decline. and partial payments are on the roadmap

**Priya Shah** 09:45
I'll take the frontend side. key per attempt, kept in sessionStorage, no silent retries, and the error message has to stop telling people to try again

**Alex Chen** 09:58
one more hard question: if all retries time out and we don't know if it charged? I say block that key and show "still checking". a stuck payment is a support ticket. a double charge is an incident

**Maria Lopez** 10:04
agree, though support will need a way to unblock those. we should build that

**Alex Chen** 10:05
yes. follow-up

---

## Thread 5: JWT expiry after the security review

**Channel:** #security
**Date:** 2026-06-08 to 2026-06-09
**People:** Maria Lopez, Sam Patel, Priya Shah, Alex Chen
**Outcome:** Access tokens go from 60 to 15 minutes, with rotating refresh tokens. Shipped in PR #6.

**Maria Lopez** 2026-06-08 15:10
report's in from the security review (SEC-2026-Q2). the one that matters is F-03, rated High. they kept using a token after logout and could still hit payment routes for the rest of its 60 minutes. and one customer's SOC 2 questionnaire means we need Highs closed in 30 days, so July 8

**Sam Patel** 15:18
that's because the gateway verifies the JWT offline for payment routes. only dashboard routes check the session

**Alex Chen** 15:24
which was deliberate, I wanted taking payments to keep working when auth is having problems. I still think that's right, but it means token lifetime is the only limit on a leaked token

**Maria Lopez** 15:30
options: shorter tokens with refresh, or check a denylist in redis on payment routes

**Sam Patel** 15:36
denylist puts redis in the payment path. right now if redis fails over you log in again. I want that to stay the worst case

**Alex Chen** 15:38
+1. no redis on the payment path

**Maria Lopez** 15:44
so shorter tokens. how short? I was thinking 5 min

**Priya Shah** 15:52
5 means a refresh mid-form for anyone on a flaky connection. accounts teams leave invoice pages open for ages and hotel wifi exists. what does the report ask for?

**Maria Lopez** 15:58
"15 minutes or less" closes it

**Priya Shah** 16:01
then 15 please. I can make refresh silent so nobody notices

**Sam Patel** 2026-06-09 09:12
should refresh tokens rotate? report recommends it

**Maria Lopez** 09:20
yes, with reuse detection. old token shows up, we kill the session. stored as a hash in the session in redis

**Priya Shah** 09:31
then I need single-flight on the client. three requests hit a 401 at once, three refreshes with the same token, and the user's logged out. noted

**Priya Shah** 09:33
also what about binding tokens to IP, it's in the report as optional

**Maria Lopez** 09:38
customers are on VPNs, IPs change mid session. false logouts all day, no

**Maria Lopez** 09:40
decided then: 15 min, rotating refresh, session idle stays at 8h. I'll write it up with Sam. PR next week
