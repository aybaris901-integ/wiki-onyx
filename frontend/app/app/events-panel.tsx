"use client";

import { useEffect, useState, type CSSProperties } from "react";
import { relativeTime, useEvents, type BrainEvent, type EventType } from "@/lib/events";
import { Markdown } from "@/lib/markdown";
import { SourceCard, inStoryOrder } from "./sources";

// The live events rail: what Triggerware-style triggers just did.
// A right-hand rail on wide screens, a bottom sheet behind a button on phones.

const ICON: Record<EventType, string> = {
  employee_left: "👋",
  handoff_report: "📦",
  new_hire: "🌱",
  onboarding_plan: "🗺️",
  pr_merged: "🔀",
  pr_missing_why: "❓",
  info: "•",
};

const BADGE: Partial<Record<EventType, string>> = {
  handoff_report: "Handoff report",
  onboarding_plan: "Onboarding plan",
  pr_missing_why: "Needs a why",
};

const TONE = { warn: "coral", good: "leaf", info: "sky" } as const;

export function EventsPanel() {
  const { events, connection, sample } = useEvents();
  const [open, setOpen] = useState(false);
  const [now, setNow] = useState(0);
  const [seen, setSeen] = useState(0);

  useEffect(() => {
    setNow(Date.now());
    const timer = setInterval(() => setNow(Date.now()), 10_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (open) setSeen(events.length);
  }, [open, events.length]);

  const unseen = Math.max(0, events.length - seen);
  const label =
    connection === "live" ? "Live" : connection === "polling" ? "Checking every 3 s" : connection === "offline" ? "Offline" : "Connecting";

  return (
    <>
      <button
        type="button"
        className="ap-mark ap-over ap-events-toggle"
        aria-expanded={open}
        aria-controls="live-events"
        onClick={() => setOpen((value) => !value)}
      >
        <i className={`ap-dot ap-dot-${connection}`} aria-hidden="true" />
        Events
        {unseen > 0 && !open && <span className="ap-badge">{unseen}</span>}
      </button>

      <aside id="live-events" className="ap-events" data-open={open || undefined} aria-label="Live events">
        <div className="ap-events-head">
          <h2 className="ap-events-title">
            <i className={`ap-dot ap-dot-${connection}`} aria-hidden="true" />
            Live events
          </h2>
          <span className="ap-events-state">
            {label}
            {sample && " · sample"}
          </span>
          <button type="button" className="ap-events-close" onClick={() => setOpen(false)} aria-label="Close events">
            ×
          </button>
        </div>
        {events.length === 0 ? (
          <p className="ap-events-empty">
            {connection === "offline"
              ? "The agent's event feed isn't reachable. Events will show here when it is."
              : "Nothing yet. When someone joins, leaves, or merges a PR without a why, it shows up here."}
          </p>
        ) : (
          <ol className="ap-events-list">
            {events.map((event, index) => (
              <EventCard key={event.id} event={event} index={index} now={now} />
            ))}
          </ol>
        )}
      </aside>
    </>
  );
}

function EventCard({ event, index, now }: { event: BrainEvent; index: number; now: number }) {
  const report = event.type === "handoff_report" || event.type === "onboarding_plan";
  const [expanded, setExpanded] = useState(report);
  const tone = TONE[event.severity];
  const badge = BADGE[event.type];
  const hasMore = event.body.trim().length > 0 || event.sources.length > 0;

  return (
    <li
      className={`ap-event tone-${tone}`}
      data-type={event.type}
      data-expanded={expanded || undefined}
      style={{ "--i": Math.min(index, 6) } as CSSProperties}
    >
      <button
        type="button"
        className="ap-event-head"
        aria-expanded={expanded}
        disabled={!hasMore}
        onClick={() => setExpanded((value) => !value)}
      >
        <span className="ap-event-icon" aria-hidden="true">
          {ICON[event.type]}
        </span>
        <span className="ap-event-text">
          {badge && <span className="ap-event-badge">{badge}</span>}
          <strong className="ap-event-title">{event.title}</strong>
          <span className="ap-event-meta">
            {event.person && <span>{event.person}</span>}
            <time dateTime={event.at}>{relativeTime(event.at, now)}</time>
          </span>
        </span>
        {hasMore && (
          <span className="ap-event-chev" aria-hidden="true">
            {expanded ? "–" : "+"}
          </span>
        )}
      </button>
      {expanded && hasMore && (
        <div className="ap-event-body">
          <Markdown text={event.body} className="ap-md" />
          {event.sources.length > 0 && (
            <ul className="ap-srcs ap-srcs-compact" aria-label="Sources">
              {inStoryOrder(event.sources).map((source, i) => (
                <SourceCard key={`${source.url}-${i}`} source={source} index={i} compact />
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}
