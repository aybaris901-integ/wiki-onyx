---
type: slack
title: "#payments: double charges during the sale, do we queue?"
author: Tomas Ruiz
date: 2025-11-17
channel: "#payments"
participants: [Tomas Ruiz, Maya Okafor, Priya Raman, Jordan Lee, Dana Whitlock]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/payments-2025-11-17-retry-queue.md
pr: retry-queue
---

**Tomas Ruiz** (09:12): Support has 40 tickets since Saturday, all the same thing: card charged twice, one order. Anyone looking?

**Maya Okafor** (09:15): Me. It's the provider. Their p99 went from 800ms to 14s during the sale. Our charge call times out at 10s, we catch the timeout and retry inline. Both charges go through.

**Priya Raman** (09:17): Can we just stop retrying on timeout and show the customer an error?

**Maya Okafor** (09:19): Then we lose the order, and half the time the first charge did succeed, so now we charged them and have no order. Worse.

**Tomas Ruiz** (09:23): If the provider times out and we retry, we charge them again. It has to be a queue. Write the order, enqueue the charge with an idempotency key on the order id, let a worker retry with backoff. The provider dedupes on the key.

**Dana Whitlock** (09:26): Do we need a new piece of infra for this? I'd rather not stand up Redis or SQS this week.

**Tomas Ruiz** (09:28): No. Postgres table, SELECT ... FOR UPDATE SKIP LOCKED. We already have Postgres. One table, one worker.

**Jordan Lee** (09:31): How many orders so far?

**Maya Okafor** (09:34): 212 double charged as of this morning. Refunds are going out today.

**Jordan Lee** (09:35): OK. Maya, can you have the queue version up this week? Tomas reviews. We stop inline retries today, even if that means a few lost orders until the queue ships.

**Maya Okafor** (09:37): Yes. Killing the inline retry now, queue PR by Wednesday.

**Priya Raman** (09:40): I'll write the incident review for Tuesday. For the record I was wrong about "just show an error", the key point is we can't know if the first charge happened.

**Tomas Ruiz** (09:41): That's exactly it. A timeout is not a failure, it's an unknown. Treat unknowns as "charge once, later".
