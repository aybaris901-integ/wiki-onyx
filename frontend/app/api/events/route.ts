import { connection } from "next/server";
import { forward } from "@/lib/backend";
import { readEvent } from "@/lib/events";
import { sampleEvents } from "@/lib/sample-store";

// GET: the latest events, newest first. Sample events when no agent is configured.
export async function GET() {
  await connection();
  try {
    const reply = await forward("/events");
    if (!reply) return Response.json({ events: sampleEvents(), sample: true });
    if (!reply.ok) return Response.json({ error: "The agent returned an error." }, { status: 503 });
    const data = await reply.json().catch(() => null);
    const events = (Array.isArray(data?.events) ? data.events : []).map(readEvent).filter(Boolean);
    return Response.json({ events });
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}

// POST: pass a Triggerware-style webhook on to the agent.
export async function POST(request: Request) {
  const body = await request.text();
  try {
    const reply = await forward("/events", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
    });
    if (!reply) return Response.json({ error: "No agent is connected, so events can't be posted." }, { status: 503 });
    return new Response(await reply.text(), {
      status: reply.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}
