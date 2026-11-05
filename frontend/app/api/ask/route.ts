import { MAX_QUESTION, readAnswer } from "@/lib/answer";
import { sampleAnswer } from "@/lib/mock";

// The page always talks to this route. With ASK_BACKEND_URL set it forwards to the
// real agent's POST /ask. Without it, it returns stand-in replies marked as samples.

const WAIT_FOR_AGENT_MS = 30_000;

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const question =
    typeof body?.question === "string" ? body.question.trim().slice(0, MAX_QUESTION) : "";

  if (!question) {
    return Response.json({ error: "Type a question first." }, { status: 400 });
  }

  const backend = process.env.ASK_BACKEND_URL;

  if (!backend) {
    await new Promise((done) => setTimeout(done, 900 + Math.random() * 800));
    return Response.json(sampleAnswer(question));
  }

  try {
    const reply = await fetch(`${backend.replace(/\/+$/, "")}/ask`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question }),
      signal: AbortSignal.timeout(WAIT_FOR_AGENT_MS),
      cache: "no-store",
    });

    if (reply.status === 429) {
      return Response.json({ error: "Too many questions." }, { status: 429 });
    }
    if (!reply.ok) {
      return Response.json({ error: "The agent returned an error." }, { status: 503 });
    }

    const answer = readAnswer(await reply.json().catch(() => null));
    if (!answer) {
      return Response.json({ error: "The agent's reply doesn't match the contract." }, { status: 502 });
    }
    return Response.json(answer);
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}
