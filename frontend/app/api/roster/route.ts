import { forward } from "@/lib/backend";
import { readPerson } from "@/lib/events";
import { sampleRoster } from "@/lib/sample-store";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const reply = await forward("/roster");
    if (!reply) return Response.json({ people: sampleRoster(), sample: true });
    if (!reply.ok) return Response.json({ error: "The agent returned an error." }, { status: 503 });
    const data = await reply.json().catch(() => null);
    const people = (Array.isArray(data?.people) ? data.people : []).map(readPerson).filter(Boolean);
    return Response.json({ people });
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}
