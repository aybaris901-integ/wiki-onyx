import type { Answer } from "./answer";

// Stand-in replies, only used until ASK_BACKEND_URL points at the real agent.
// The page stamps each of these "Sample answer". Links go to example.com on purpose.

const samples: Record<string, Answer> = {
  "why do payments go through a queue?": {
    answer:
      "Because charging customers directly caused double charges when the payment provider timed out during the November 2025 sale. Maya Okafor moved charges into a retry queue so each order is only charged once, and Priya Raman owns that service now.",
    sources: [
      {
        type: "pr",
        url: "https://example.com/ferrowen/shop/pull/482",
        author: "Maya Okafor",
        date: "2025-11-19",
        title: "Move charges into a retry queue",
        quote: "Retrying inline is what double charged 212 orders last week.",
      },
      {
        type: "slack",
        url: "https://example.com/slack/payments/p1763391",
        author: "Tomas Ruiz",
        date: "2025-11-17",
        quote: "If the provider times out and we retry, we charge them again. It has to be a queue.",
      },
      {
        type: "code",
        url: "https://example.com/ferrowen/shop/blob/main/services/payments/retry_queue.ts",
        author: "Maya Okafor",
        date: "2025-11-19",
      },
      {
        type: "owner",
        url: "https://example.com/ferrowen/shop/blob/main/CODEOWNERS",
        author: "Priya Raman",
        date: "2026-03-02",
      },
    ],
  },
  "who owns the checkout service now?": {
    answer:
      "Priya Raman has owned it since March 2026, when Tomas Ruiz left the company. Tomas wrote most of it, so his handover notes are the best place to start.",
    sources: [
      {
        type: "owner",
        url: "https://example.com/ferrowen/shop/blob/main/CODEOWNERS",
        author: "Priya Raman",
        date: "2026-03-02",
      },
      {
        type: "doc",
        url: "https://example.com/wiki/checkout-handover-notes",
        author: "Tomas Ruiz",
        date: "2026-02-26",
      },
    ],
  },
  "why do we still run our own image server?": {
    answer:
      "The team priced a hosted service in June 2024 and it would have cost four times as much at our catalog size. They agreed to look again if traffic doubled, and it hasn't.",
    sources: [
      {
        type: "slack",
        url: "https://example.com/slack/infra/p1718902",
        author: "Dana Whitlock",
        date: "2024-06-20",
      },
      {
        type: "commit",
        url: "https://example.com/ferrowen/shop/commit/9f3c2ab71d",
        author: "Dana Whitlock",
        date: "2024-06-24",
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
