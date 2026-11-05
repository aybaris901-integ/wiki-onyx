// The team's API contract: POST /ask -> { answer, sources: [{ type, url, author, date }] }
// title and quote are optional extras the page shows when the agent sends them.

export type Source = {
  type: string;
  url: string;
  author: string;
  date: string;
  title?: string;
  quote?: string;
};

export type AnswerMeta = {
  retriever?: string;
  model?: string;
  ms?: number;
  live?: boolean;
};

export type Answer = {
  answer: string;
  sources: Source[];
  sample?: boolean;
  meta?: AnswerMeta;
};

export const MAX_QUESTION = 500;

// Swap these for the real demo questions once the made-up company is ready.
export const EXAMPLE_QUESTIONS = [
  "Why do payments go through a retry queue?",
  "Who owns the image server now?",
  "Why don't we use Elasticsearch for search?",
];

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

// Only web links can be opened from a card, so a bad link from the agent can't run anything.
function webLink(value: unknown): string {
  try {
    const url = new URL(text(value));
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : "";
  } catch {
    return "";
  }
}

// Returns null when the agent's reply doesn't match the contract.
export function readAnswer(data: unknown): Answer | null {
  if (!data || typeof data !== "object") return null;
  const reply = data as { answer?: unknown; sources?: unknown; meta?: unknown };
  const answer = text(reply.answer);
  if (!answer) return null;

  const sources = (Array.isArray(reply.sources) ? reply.sources : [])
    .filter((item) => item && typeof item === "object")
    .map((item: Record<string, unknown>) => ({
      type: text(item.type),
      url: webLink(item.url),
      author: text(item.author),
      date: text(item.date),
      title: text(item.title) || undefined,
      quote: text(item.quote) || undefined,
    }));

  return { answer, sources, meta: readMeta(reply.meta) };
}

function readMeta(value: unknown): AnswerMeta | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const meta: AnswerMeta = {
    retriever: text(raw.retriever) || undefined,
    model: text(raw.model) || undefined,
    ms: typeof raw.ms === "number" && Number.isFinite(raw.ms) ? raw.ms : undefined,
    live: raw.live === true ? true : undefined,
  };
  return Object.values(meta).some((entry) => entry !== undefined) ? meta : undefined;
}
