import { forward } from "@/lib/backend";
import { readEvent, readPerson, type PersonStatus } from "@/lib/schema";
import { sampleSetStatus } from "@/lib/sample-store";

const STATUSES: PersonStatus[] = ["active", "left", "new"];

export async function POST(request: Request, { params }: { params: Promise<{ handle: string }> }) {
  const { handle } = await params;
  const body = await request.json().catch(() => null);
  const status = body?.status as PersonStatus;
  if (!handle || !STATUSES.includes(status)) {
    return Response.json({ error: "Send { status: 'left' | 'active' | 'new' }." }, { status: 400 });
  }

  try {
    const reply = await forward(`/roster/${encodeURIComponent(handle)}/status`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!reply) {
      const result = sampleSetStatus(handle, status);
      if (!result) return Response.json({ error: "No one on the roster has that handle." }, { status: 404 });
      return Response.json({ ...result, sample: true });
    }
    if (reply.status === 404) return Response.json({ error: "No one on the roster has that handle." }, { status: 404 });
    if (!reply.ok) return Response.json({ error: "The agent returned an error." }, { status: 503 });
    const data = await reply.json().catch(() => null);
    return Response.json({
      person: readPerson(data?.person),
      events: (Array.isArray(data?.events) ? data.events : []).map(readEvent).filter(Boolean),
    });
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}
