import type { BrainEvent, Person, PersonStatus } from "./schema";
import {
  SAMPLE_ROSTER,
  sampleHandoffEvent,
  sampleHireEvent,
  sampleLeftEvent,
  sampleOnboardingEvent,
  sampleStartingEvents,
} from "./mock";

// In-memory stand-in for the agent's roster and events, used only without ASK_BACKEND_URL.
// Lives on globalThis so dev-server reloads don't lose the demo state mid-presentation.

type Listener = (event: BrainEvent) => void;

type Store = {
  roster: Person[];
  events: BrainEvent[];
  listeners: Set<Listener>;
  timers: Set<ReturnType<typeof setTimeout>>;
};

const REPORT_DELAY_MS = 3200;
const MAX = 50;

const slot = globalThis as unknown as { __brainSampleStore?: Store };

function fresh(): Store {
  return {
    roster: SAMPLE_ROSTER.map((person) => ({ ...person })),
    events: sampleStartingEvents(),
    listeners: new Set(),
    timers: new Set(),
  };
}

function store(): Store {
  if (!slot.__brainSampleStore) slot.__brainSampleStore = fresh();
  return slot.__brainSampleStore;
}

export function sampleRoster(): Person[] {
  return store().roster;
}

export function sampleEvents(): BrainEvent[] {
  return store().events;
}

export function subscribeSample(listener: Listener): () => void {
  store().listeners.add(listener);
  return () => store().listeners.delete(listener);
}

function push(event: BrainEvent): BrainEvent {
  const s = store();
  s.events = [event, ...s.events].slice(0, MAX);
  for (const listener of s.listeners) listener(event);
  return event;
}

function later(ms: number, run: () => void) {
  const s = store();
  const timer = setTimeout(() => {
    s.timers.delete(timer);
    run();
  }, ms);
  s.timers.add(timer);
}

export function sampleSetStatus(handle: string, status: PersonStatus): { person: Person; events: BrainEvent[] } | null {
  const s = store();
  const person = s.roster.find((entry) => entry.handle === handle);
  if (!person) return null;
  const today = new Date().toISOString().slice(0, 10);
  person.status = status;
  if (status === "left") person.left = today;
  else person.left = undefined;
  if (status === "new") person.started = today;

  const now = new Date().toISOString();
  const events: BrainEvent[] = [];
  if (status === "left") {
    events.push(push(sampleLeftEvent(person, now)));
    later(REPORT_DELAY_MS, () => push(sampleHandoffEvent({ ...person }, new Date().toISOString())));
  } else if (status === "new") {
    events.push(push(sampleHireEvent(person, now)));
    later(REPORT_DELAY_MS, () => push(sampleOnboardingEvent({ ...person }, new Date().toISOString())));
  }
  return { person, events };
}

export function sampleReset() {
  const s = store();
  for (const timer of s.timers) clearTimeout(timer);
  const listeners = s.listeners;
  slot.__brainSampleStore = { ...fresh(), listeners };
}
