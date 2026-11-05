import { backendUrl } from "@/lib/backend";
import type { BrainEvent } from "@/lib/events";
import { sampleEvents, subscribeSample } from "@/lib/sample-store";

export const dynamic = "force-dynamic";

const SSE_HEADERS = {
  "content-type": "text/event-stream; charset=utf-8",
  "cache-control": "no-cache, no-transform",
  connection: "keep-alive",
  "x-accel-buffering": "no",
};

const encoder = new TextEncoder();
const line = (event: BrainEvent) => encoder.encode(`data: ${JSON.stringify(event)}\n\n`);

// GET: live events. Proxies the agent's stream, or serves the sample store's.
export async function GET(request: Request) {
  const backend = backendUrl();

  if (!backend) {
    let stop: (() => void) | undefined;
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode(": sample stream\n\n"));
        for (const event of [...sampleEvents()].reverse()) controller.enqueue(line(event));
        const unsubscribe = subscribeSample((event) => {
          try {
            controller.enqueue(line(event));
          } catch {
            stop?.();
          }
        });
        const beat = setInterval(() => {
          try {
            controller.enqueue(encoder.encode(": keep-alive\n\n"));
          } catch {
            stop?.();
          }
        }, 15_000);
        stop = () => {
          unsubscribe();
          clearInterval(beat);
          try {
            controller.close();
          } catch {
            // Already closed.
          }
        };
        request.signal.addEventListener("abort", () => stop?.());
      },
      cancel() {
        stop?.();
      },
    });
    return new Response(stream, { headers: SSE_HEADERS });
  }

  try {
    const upstream = await fetch(`${backend}/events/stream`, {
      headers: { accept: "text/event-stream" },
      cache: "no-store",
      signal: request.signal,
    });
    if (!upstream.ok || !upstream.body) {
      return Response.json({ error: "The agent's event stream isn't available." }, { status: 503 });
    }
    return new Response(upstream.body, { headers: SSE_HEADERS });
  } catch {
    return Response.json({ error: "The agent didn't respond." }, { status: 503 });
  }
}
