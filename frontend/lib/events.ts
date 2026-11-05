"use client";

// Events and people, as the agent sends them (see /AGENTS.md "Events" and "Roster").

import { useEffect, useRef, useState } from "react";
import type { Source } from "./answer";

export type EventType =
  | "employee_left"
  | "handoff_report"
  | "new_hire"
  | "onboarding_plan"
  | "pr_merged"
  | "pr_missing_why"
  | "info";

export type Severity = "info" | "warn" | "good";

export type BrainEvent = {
  id: string;
  type: EventType;
  title: string;
  body: string;
  at: string;
  person?: string;
  sources: Source[];
  severity: Severity;
  sample?: boolean;
};

export type PersonStatus = "active" | "left" | "new";

export type Person = {
  name: string;
  handle: string;
  email?: string;
  role: string;
  team: string;
  status: PersonStatus;
  started?: string;
  left?: string;
  manager?: string;
};

export const MAX_EVENTS = 50;

const EVENT_TYPES: EventType[] = [
  "employee_left",
  "handoff_report",
  "new_hire",
  "onboarding_plan",
  "pr_merged",
  "pr_missing_why",
  "info",
];

function text(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function webLink(value: unknown): string {
  try {
    const url = new URL(text(value));
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : "";
  } catch {
    return "";
  }
}

export function readSources(value: unknown): Source[] {
  return (Array.isArray(value) ? value : [])
    .filter((item) => item && typeof item === "object")
    .map((item: Record<string, unknown>) => ({
      type: text(item.type),
      url: webLink(item.url),
      author: text(item.author),
      date: text(item.date),
      title: text(item.title) || undefined,
      quote: text(item.quote) || undefined,
    }));
}

// Returns null when the event doesn't match the contract.
export function readEvent(data: unknown): BrainEvent | null {
  if (!data || typeof data !== "object") return null;
  const raw = data as Record<string, unknown>;
  const id = text(raw.id);
  const title = text(raw.title);
  if (!id || !title) return null;
  const type = text(raw.type) as EventType;
  const severity = text(raw.severity) as Severity;
  return {
    id,
    type: EVENT_TYPES.includes(type) ? type : "info",
    title,
    body: text(raw.body),
    at: text(raw.at) || new Date().toISOString(),
    person: text(raw.person) || undefined,
    sources: readSources(raw.sources),
    severity: severity === "warn" || severity === "good" ? severity : "info",
    sample: raw.sample === true || undefined,
  };
}

export function readPerson(data: unknown): Person | null {
  if (!data || typeof data !== "object") return null;
  const raw = data as Record<string, unknown>;
  const name = text(raw.name);
  const handle = text(raw.handle);
  if (!name || !handle) return null;
  const status = text(raw.status) as PersonStatus;
  return {
    name,
    handle,
    email: text(raw.email) || undefined,
    role: text(raw.role),
    team: text(raw.team),
    status: status === "left" || status === "new" ? status : "active",
    started: text(raw.started) || undefined,
    left: text(raw.left) || undefined,
    manager: text(raw.manager) || undefined,
  };
}

// Newest first, no duplicates, capped.
export function mergeEvents(current: BrainEvent[], incoming: BrainEvent[]): BrainEvent[] {
  const byId = new Map<string, BrainEvent>();
  for (const event of [...incoming, ...current]) {
    if (!byId.has(event.id)) byId.set(event.id, event);
  }
  return [...byId.values()]
    .sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime())
    .slice(0, MAX_EVENTS);
}

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

export function relativeTime(iso: string, now: number): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then) || !now) return "";
  const seconds = Math.max(0, Math.round((now - then) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds} s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}
