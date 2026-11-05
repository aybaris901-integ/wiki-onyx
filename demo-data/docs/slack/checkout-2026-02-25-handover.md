---
type: slack
title: "#checkout: Tomas's last week, who owns checkout?"
author: Jordan Lee
date: 2026-02-25
channel: "#checkout"
participants: [Jordan Lee, Tomas Ruiz, Priya Raman, Maya Okafor]
url: https://github.com/aybaris901-integ/wiki-onyx/blob/company-brain/demo-data/docs/slack/checkout-2026-02-25-handover.md
pr: checkout-codeowners
---

**Jordan Lee** (10:00): Tomas's last day is Friday. We need a named owner for checkout and the payments retry queue before then. Priya, you've been the main reviewer for both since autumn. Would you take them?

**Priya Raman** (10:04): Yes, with one ask: Tomas, write down the stuff that is in your head and not in the code. The price lock, the weird tax rounding, the bits that look wrong but aren't.

**Tomas Ruiz** (10:06): Already started. docs/handoffs/tomas-checkout-handover.md, will be done Thursday. The price lock is the one that bites people.

**Maya Okafor** (10:09): I built the retry queue, shouldn't I own it?

**Jordan Lee** (10:12): You're on fraud next quarter full time. Checkout and payments live together, one owner is simpler. You stay as second reviewer.

**Maya Okafor** (10:13): Fair enough.

**Tomas Ruiz** (10:15): Priya, the only thing I'll say in public: the checkout code is mine, but the decisions were the team's. Every "why" is in an ADR or a thread. Read those before you change anything that looks silly.

**Priya Raman** (10:16): Deal. I'll update CODEOWNERS Monday after you're gone so nothing routes to you.

**Jordan Lee** (10:17): Thanks both. I'll record it in tomorrow's notes and ADR 0004.
