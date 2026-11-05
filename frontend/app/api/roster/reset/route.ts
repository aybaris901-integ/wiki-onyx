import { forward } from "@/lib/backend";
import { sampleReset } from "@/lib/sample-store";

export const dynamic = "force-dynamic";

export async function POST() {
  try {
    const reply = await forward("/roster/reset", { method: "POST" });
    if (!reply) {
      sampleReset();
      return Response.json({ ok: true, sample: true });
    }
    if (!reply.ok) return Response.json({ error: "The agent returned an error." }, { status: 503 });
    return Response.json({ ok: true });
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}
