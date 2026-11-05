import type { Answer, Source } from "./answer";
import type { BrainEvent, Person } from "./schema";

// Stand-in data, only used until ASK_BACKEND_URL points at the real agent.
// The page stamps all of it "Sample". Links open the demo data on GitHub.

const REPO = "https://github.com/aybaris901-integ/wiki-onyx";
const BLOB = `${REPO}/blob/company-brain/demo-data`;
const PULLS = `${REPO}/pulls?q=is%3Apr+`;

const samples: Record<string, Answer> = {
  "why do payments go through a retry queue?": {
    answer:
      "Because charging inline double-charged 212 orders when the payment provider timed out during the November 2025 sale. Maya Okafor moved charges into a retry queue so each order is charged exactly once, and Priya Raman owns it now.",
    sources: [
      {
        type: "slack",
        url: `${BLOB}/docs/slack/payments-2025-11-17-retry-queue.md`,
        author: "Tomas Ruiz",
        date: "2025-11-17",
        title: "#payments",
        quote: "If the provider times out and we retry, we charge them again. It has to be a queue.",
      },
      {
        type: "meeting",
        url: `${BLOB}/docs/meetings/2025-11-18-payments-incident-review.md`,
        author: "Jordan Lee",
        date: "2025-11-18",
        title: "Payments incident review",
        quote: "212 orders double charged between 02:10 and 02:40.",
      },
      {
        type: "pr",
        url: `${PULLS}Move+charges+into+a+retry+queue`,
        author: "Maya Okafor",
        date: "2025-11-19",
        title: "Move charges into a retry queue",
        quote: "Retrying inline is what double charged 212 orders last week.",
      },
      {
        type: "code",
        url: `${BLOB}/acme/services/payments/retry_queue.py`,
        author: "Maya Okafor",
        date: "2025-11-19",
      },
      {
        type: "owner",
        url: `${BLOB}/acme/CODEOWNERS`,
        author: "Priya Raman",
        date: "2026-03-02",
      },
    ],
  },
  "who owns the image server now?": {
    answer:
      "Alex Chen owns the image server and the thumbnail cron. Acme runs its own because Dana Whitlock priced a hosted CDN in June 2024 at four times the cost for our catalog size, with a note to revisit if traffic doubles.",
    sources: [
      {
        type: "slack",
        url: `${BLOB}/docs/slack/infra-2024-06-20-image-server.md`,
        author: "Dana Whitlock",
        date: "2024-06-20",
        title: "#infra",
        quote: "Hosted comes out at 4x what we pay today at our catalog size.",
      },
      {
        type: "adr",
        url: `${BLOB}/docs/adr/0003-self-hosted-image-server.md`,
        author: "Dana Whitlock",
        date: "2024-06-24",
        title: "ADR 0003: Self-hosted image server",
        quote: "Revisit if image traffic doubles.",
      },
      {
        type: "code",
        url: `${BLOB}/acme/services/images/server.py`,
        author: "Alex Chen",
        date: "2026-08-12",
      },
      {
        type: "owner",
        url: `${BLOB}/acme/CODEOWNERS`,
        author: "Alex Chen",
        date: "2025-04-10",
      },
    ],
  },
  "why don't we use elasticsearch for search?": {
    answer:
      "Alex Chen chose Postgres full-text search in April 2025 because it was one less cluster to run for a catalog our size. The decision is in ADR 0005, and Alex still owns the indexer.",
    sources: [
      {
        type: "slack",
        url: `${BLOB}/docs/slack/search-2025-04-08-postgres-vs-elastic.md`,
        author: "Alex Chen",
        date: "2025-04-08",
        title: "#search",
        quote: "One less cluster to run. We can move when the catalog is ten times bigger.",
      },
      {
        type: "adr",
        url: `${BLOB}/docs/adr/0005-postgres-full-text-search.md`,
        author: "Alex Chen",
        date: "2025-04-10",
        title: "ADR 0005: Postgres full-text search",
      },
      {
        type: "pr",
        url: `${PULLS}Postgres+full-text+search`,
        author: "Alex Chen",
        date: "2025-04-11",
        title: "Search on Postgres full-text",
      },
      {
        type: "owner",
        url: `${BLOB}/acme/CODEOWNERS`,
        author: "Alex Chen",
        date: "2025-04-10",
      },
    ],
  },
};

export function sampleAnswer(question: string): Answer {
  const match = samples[question.trim().toLowerCase()];
  return {
    ...(match ?? {
      answer: "There's no sample answer for that question yet, because the real agent isn't connected.",
      sources: [],
    }),
    sample: true,
  };
}

export const SAMPLE_ROSTER: Person[] = [
  { name: "Maya Okafor", handle: "maya", email: "maya@acme.example", role: "Senior Backend Engineer", team: "Payments", status: "active", started: "2023-02-13", manager: "Jordan Lee" },
  { name: "Tomas Ruiz", handle: "tomas", email: "tomas@acme.example", role: "Staff Engineer", team: "Checkout", status: "left", started: "2021-06-01", left: "2026-03-01", manager: "Jordan Lee" },
  { name: "Priya Raman", handle: "priya", email: "priya@acme.example", role: "Backend Engineer", team: "Checkout", status: "active", started: "2024-01-08", manager: "Jordan Lee" },
  { name: "Dana Whitlock", handle: "dana", email: "dana@acme.example", role: "Infra Lead", team: "Platform", status: "active", started: "2022-03-21", manager: "Jordan Lee" },
  { name: "Alex Chen", handle: "alex", email: "alex@acme.example", role: "Senior Engineer", team: "Images & Search", status: "active", started: "2022-09-05", manager: "Jordan Lee" },
  { name: "Jordan Lee", handle: "jordan", email: "jordan@acme.example", role: "Engineering Manager", team: "Engineering", status: "active", started: "2020-11-02" },
  { name: "Sam Patel", handle: "sam", email: "sam@acme.example", role: "Backend Engineer", team: "Backend", status: "new", started: "2026-11-02", manager: "Jordan Lee" },
];

const owner = (author: string, date: string): Source => ({
  type: "owner",
  url: `${BLOB}/acme/CODEOWNERS`,
  author,
  date,
});

export function sampleStartingEvents(now = Date.now()): BrainEvent[] {
  const at = (minutesAgo: number) => new Date(now - minutesAgo * 60_000).toISOString();
  return [
    {
      id: "evt_sample_pr_why",
      type: "pr_missing_why",
      title: "PR merged without a why: Bump image cache TTL",
      body:
        "Alex Chen merged **Bump image cache TTL** with no reason in the description. The next person to touch `services/images/server.py` won't know why the TTL changed.\n\n- Ask Alex for one sentence and add it to the PR.\n- Or link the thread where it was decided.",
      at: at(14),
      person: "Alex Chen",
      severity: "warn",
      sources: [
        { type: "pr", url: `${PULLS}Bump+image+cache+TTL`, author: "Alex Chen", date: "2026-10-30", title: "Bump image cache TTL" },
      ],
      sample: true,
    },
    {
      id: "evt_sample_pr_merged",
      type: "pr_merged",
      title: "PR merged: Fix thumbnail cron double run",
      body: "Alex Chen merged **Fix thumbnail cron double run**. The why is in the description and linked to the #images thread from Aug 12.",
      at: at(52),
      person: "Alex Chen",
      severity: "good",
      sources: [
        { type: "pr", url: `${PULLS}Fix+thumbnail+cron+double+run`, author: "Alex Chen", date: "2026-08-13", title: "Fix thumbnail cron double run" },
        { type: "slack", url: `${BLOB}/docs/slack/images-2026-08-12-thumbnail-cron-outage.md`, author: "Alex Chen", date: "2026-08-12", title: "#images" },
      ],
      sample: true,
    },
    {
      id: "evt_sample_new_hire",
      type: "new_hire",
      title: "Sam Patel joined Acme",
      body: "Sam Patel started on the Backend team on Nov 2, 2026, reporting to Jordan Lee. An onboarding plan is ready on the Team page.",
      at: at(170),
      person: "Sam Patel",
      severity: "good",
      sources: [{ type: "doc", url: `${BLOB}/team-roster.csv`, author: "Jordan Lee", date: "2026-11-02", title: "team-roster.csv" }],
      sample: true,
    },
  ];
}

let counter = 0;
export function sampleEventId(): string {
  counter += 1;
  return `evt_sample_${Date.now().toString(36)}_${counter}`;
}

export function sampleLeftEvent(person: Person, at: string): BrainEvent {
  return {
    id: sampleEventId(),
    type: "employee_left",
    title: `${person.name} left Acme`,
    body: `${person.name} (${person.role}, ${person.team}) was marked as left. Writing their handoff report from their pull requests, Slack threads and the systems they own.`,
    at,
    person: person.name,
    severity: "warn",
    sources: [{ type: "doc", url: `${BLOB}/team-roster.csv`, author: "Jordan Lee", date: at.slice(0, 10), title: "team-roster.csv" }],
    sample: true,
  };
}

export function sampleHandoffEvent(person: Person, at: string): BrainEvent {
  const alex = person.handle === "alex";
  const body = alex
    ? [
        "## What Alex owned",
        "- **Image server** (`services/images/server.py`): self-hosted since June 2024, 4x cheaper than hosted at our catalog size.",
        "- **Thumbnail cron** (`services/images/thumbnail_cron.py`): runs 02:00 UTC, fixed the double-run outage of Aug 12, 2026 alone.",
        "- **Search indexer** (`services/search/indexer.py`): Postgres full-text, ADR 0005.",
        "",
        "## Open risks",
        "- The thumbnail cron has no alert when it skips a night. Alex noticed by eye.",
        "- Image cache TTL was bumped on Oct 30, 2026 with no written reason.",
        "",
        "## Who takes over",
        "- **Dana Whitlock** for the image server and cron (Platform already runs the boxes).",
        "- **Priya Raman** for the search indexer.",
        "",
        "## Runbooks",
        "- Thumbnail cron re-run: `uv run python -m services.images.thumbnail_cron --since <date>`",
        "- Search reindex: see the #search thread from Apr 8, 2025.",
        "",
        "## Things only Alex knew",
        "1. The image server's disk fills at ~92% every quarter. Alex pruned by hand.",
        "2. Search ranking weights were tuned against the top 200 queries of March 2025, never since.",
        "3. The cron's lock file lives in `/var/tmp`, which is wiped on reboot.",
      ].join("\n")
    : [
        `## What ${person.name} owned`,
        `- Work on the ${person.team} team as ${person.role}.`,
        "",
        "## Who takes over",
        `- ${person.manager ?? "Jordan Lee"} to assign an owner this week.`,
        "",
        "## Open risks",
        "- No handoff doc was found for this person. Ask them for one before their last day.",
      ].join("\n");

  return {
    id: sampleEventId(),
    type: "handoff_report",
    title: `Handoff report for ${person.name}`,
    body,
    at,
    person: person.name,
    severity: "info",
    sources: alex
      ? [
          { type: "doc", url: `${BLOB}/docs/handoffs/alex-offboarding.md`, author: "Alex Chen", date: at.slice(0, 10), title: "Alex's offboarding handoff" },
          { type: "slack", url: `${BLOB}/docs/slack/images-2026-08-12-thumbnail-cron-outage.md`, author: "Alex Chen", date: "2026-08-12", title: "#images" },
          { type: "adr", url: `${BLOB}/docs/adr/0005-postgres-full-text-search.md`, author: "Alex Chen", date: "2025-04-10", title: "ADR 0005" },
          { type: "code", url: `${BLOB}/acme/services/images/server.py`, author: "Alex Chen", date: "2026-08-12" },
          owner("Dana Whitlock", at.slice(0, 10)),
        ]
      : [owner(person.manager ?? "Jordan Lee", at.slice(0, 10))],
    sample: true,
  };
}

export function sampleHireEvent(person: Person, at: string): BrainEvent {
  return {
    id: sampleEventId(),
    type: "new_hire",
    title: `${person.name} joined Acme`,
    body: `${person.name} starts on the ${person.team} team as ${person.role}. Building an onboarding plan from the ADRs and current owners.`,
    at,
    person: person.name,
    severity: "good",
    sources: [{ type: "doc", url: `${BLOB}/team-roster.csv`, author: "Jordan Lee", date: at.slice(0, 10), title: "team-roster.csv" }],
    sample: true,
  };
}

export function sampleOnboardingEvent(person: Person, at: string): BrainEvent {
  return {
    id: sampleEventId(),
    type: "onboarding_plan",
    title: `Onboarding plan for ${person.name}`,
    body: [
      "## Week 1: how Acme works",
      "- Read ADR 0001 (retry queue), 0003 (image server), 0005 (search). Each says why, not just what.",
      "- Pair with **Priya Raman** on checkout and payments.",
      "",
      "## Week 2: ship something small",
      "- Pick a `good-first-issue` in payments. Maya Okafor reviews.",
      "- Every PR needs a **Why** section. The brain flags the ones that don't.",
      "",
      "## Week 3: own a corner",
      "- Shadow Dana Whitlock on the image server and the thumbnail cron.",
      "- Ask the brain before asking a person. Then ask the person anyway.",
    ].join("\n"),
    at,
    person: person.name,
    severity: "good",
    sources: [
      { type: "adr", url: `${BLOB}/docs/adr/0001-retry-queue.md`, author: "Maya Okafor", date: "2025-11-19", title: "ADR 0001" },
      { type: "adr", url: `${BLOB}/docs/adr/0003-self-hosted-image-server.md`, author: "Dana Whitlock", date: "2024-06-24", title: "ADR 0003" },
      { type: "adr", url: `${BLOB}/docs/adr/0005-postgres-full-text-search.md`, author: "Alex Chen", date: "2025-04-10", title: "ADR 0005" },
      owner("Priya Raman", "2026-03-02"),
    ],
    sample: true,
  };
}
