// Where the real agent lives. Unset means sample mode.
export function backendUrl(): string | null {
  const raw = process.env.ASK_BACKEND_URL?.trim();
  return raw ? raw.replace(/\/+$/, "") : null;
}

export const WAIT_FOR_AGENT_MS = 30_000;

export async function forward(path: string, init?: RequestInit): Promise<Response | null> {
  const backend = backendUrl();
  if (!backend) return null;
  return fetch(`${backend}${path}`, {
    ...init,
    cache: "no-store",
    signal: init?.signal ?? AbortSignal.timeout(WAIT_FOR_AGENT_MS),
  });
}
