"use client";

// Live events hook for the client. Pure helpers live in ./schema.

import { useEffect, useRef, useState } from "react";
import { mergeEvents, readEvent, MAX_EVENTS, type BrainEvent } from "./schema";

export * from "./schema";

export type Connection = "connecting" | "live" | "polling" | "offline";

// Live events from the agent: a stream first, polling when the stream can't be kept open.
export function useEvents() {
  const [events, setEvents] = useState<BrainEvent[]>([]);
  const [connection, setConnection] = useState<Connection>("connecting");
  const [sample, setSample] = useState(false);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    let source: EventSource | null = null;
    let poll: ReturnType<typeof setInterval> | null = null;
    let failures = 0;

    const take = (data: unknown) => {
      const list = Array.isArray(data) ? data : [data];
      const parsed = list.map(readEvent).filter((event): event is BrainEvent => event !== null);
      if (parsed.length === 0) return;
      if (parsed.some((event) => event.sample)) setSample(true);
      setEvents((current) => mergeEvents(current, parsed));
    };

    const fetchList = async () => {
      try {
        const response = await fetch("/api/events", { cache: "no-store" });
        if (!response.ok) throw new Error(String(response.status));
        const data = await response.json();
        if (data?.sample) setSample(true);
        take(data?.events ?? []);
        failures = 0;
        if (alive.current && !source) setConnection("polling");
      } catch {
        failures += 1;
        if (alive.current && failures >= 2) setConnection("offline");
      }
    };

    const startPolling = () => {
      if (poll) return;
      setConnection("polling");
      void fetchList();
      poll = setInterval(fetchList, 3000);
    };

    const startStream = () => {
      if (typeof EventSource === "undefined") {
        startPolling();
        return;
      }
      source = new EventSource("/api/events/stream");
      source.onopen = () => {
        if (!alive.current) return;
        setConnection("live");
        if (poll) {
          clearInterval(poll);
          poll = null;
        }
      };
      source.onmessage = (message) => {
        try {
          take(JSON.parse(message.data));
        } catch {
          // Ignore lines that aren't JSON (comments, keep-alives).
        }
      };
      source.onerror = () => {
        source?.close();
        source = null;
        if (alive.current) startPolling();
      };
    };

    void fetchList();
    startStream();

    return () => {
      alive.current = false;
      source?.close();
      if (poll) clearInterval(poll);
    };
  }, []);

  return { events, connection, sample };
}

