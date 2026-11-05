"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { flushSync } from "react-dom";
import Link from "next/link";
import { EXAMPLE_QUESTIONS, MAX_QUESTION, type Answer } from "@/lib/answer";
import { EventsPanel } from "./events-panel";
import { SourceCard, inStoryOrder } from "./sources";

type Turn = {
  id: number;
  question: string;
  state: "asking" | "answered" | "failed";
  startedAt: number;
  seconds?: number;
  reply?: Answer;
  problem?: string;
};

const SERVICE_DOWN = "The answer service isn't responding. Try again in a minute.";
const TOO_MANY = "That's a lot of questions at once. Try again in a minute.";
const UNREADABLE = "The answer service sent back something this page can't read. Try again in a minute.";

const EASE = "cubic-bezier(0.16, 1, 0.3, 1)";

export function Ask() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [leaving, setLeaving] = useState(false);
  const form = useRef<HTMLFormElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const opener = useRef<HTMLDivElement>(null);
  const chips = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);
  const started = turns.length > 0;
  const busy = turns.some((turn) => turn.state === "asking");

  // First question: the big headline flies off and the question bar drops to the bottom.
  function launch(commit: () => void) {
    const bar = form.current;
    if (!bar || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      flushSync(commit);
      return;
    }
    const from = bar.getBoundingClientRect();
    for (const part of [opener.current, chips.current]) {
      if (!part) continue;
      const box = part.getBoundingClientRect();
      Object.assign(part.style, {
        position: "fixed",
        top: `${box.top}px`,
        left: `${box.left}px`,
        width: `${box.width}px`,
        margin: "0",
      });
    }
    flushSync(() => {
      setLeaving(true);
      commit();
    });
    const to = bar.getBoundingClientRect();
    bar.animate(
      [{ transform: `translate(${from.left - to.left}px, ${from.top - to.top}px)` }, { transform: "none" }],
      { duration: 900, easing: EASE },
    );
    window.setTimeout(() => setLeaving(false), 620);
  }

  async function ask(text: string, retryId?: number) {
    const question = text.trim().slice(0, MAX_QUESTION);
    if (!question) input.current?.focus();
    if (!question || busy) return;

    const id = retryId ?? nextId.current++;
    const startedAt = performance.now();
    const update = (change: Partial<Turn>) =>
      setTurns((all) => all.map((turn) => (turn.id === id ? { ...turn, ...change } : turn)));

    const commit = () => {
      setDraft("");
      if (retryId) update({ state: "asking", startedAt, problem: undefined });
      else setTurns((all) => [...all, { id, question, state: "asking", startedAt }]);
    };
    if (started) flushSync(commit);
    else launch(commit);

    document.querySelector(`[data-turn="${id}"]`)?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      block: "start",
    });
    if (window.matchMedia("(pointer: fine)").matches) input.current?.focus({ preventScroll: true });

    let change: Partial<Turn>;
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const seconds = (performance.now() - startedAt) / 1000;
      const data = await response.json().catch(() => null);
      if (response.ok && data?.answer) change = { state: "answered", reply: data, seconds };
      else if (response.status === 429) change = { state: "failed", problem: TOO_MANY };
      else if (response.status === 502) change = { state: "failed", problem: UNREADABLE };
      else change = { state: "failed", problem: SERVICE_DOWN };
    } catch {
      change = { state: "failed", problem: SERVICE_DOWN };
    }
    update(change);
  }

  function startOver() {
    setTurns([]);
    setDraft("");
    window.scrollTo({ top: 0 });
  }

  const latest = turns[turns.length - 1]?.state;
  const phase = !started ? "open" : latest === "asking" ? "thinking" : "settled";

  return (
    <div className="ap" data-phase={phase}>
      <div className="ap-world" aria-hidden="true">
        <img className="ap-sky" src="/world/sky-clear.webp" alt="" />
        <img className="ap-puff ap-puff-a" src="/world/cloud-a.webp" alt="" />
        <img className="ap-puff ap-puff-c" src="/world/cloud-c.webp" alt="" />
        <div className="ap-brain">
          <img src="/world/brain.webp" alt="" />
        </div>
        <div className="ap-ground">
          <div className="ap-trees" />
          <img className="ap-hq" src="/world/hq.webp" alt="" />
        </div>
      </div>

      <header className="ap-top">
        <Link className="ap-mark" href="/">
          Company Brain
        </Link>
        <nav className="ap-nav" aria-label="Pages">
          {started && (
            <button type="button" className="ap-mark ap-over" disabled={busy} onClick={startOver}>
              Start over
            </button>
          )}
          <Link className="ap-mark ap-over" href="/team">
            Team
          </Link>
        </nav>
      </header>

      {(!started || leaving) && (
        <div ref={opener} className="ap-open" data-leaving={leaving || undefined}>
          <h1 className="ap-title">
            <span className="ap-line">
              <span style={{ "--l": 0 } as CSSProperties}>Ask</span>
            </span>{" "}
            <span className="ap-line">
              <span style={{ "--l": 1 } as CSSProperties}>the brain.</span>
            </span>
          </h1>
        </div>
      )}

      {started && (
        <main className="ap-thread" aria-live="polite">
          {turns.map((turn) => (
            <article key={turn.id} className="ap-turn" data-turn={turn.id}>
              <section className="ap-panel" data-state={turn.state}>
                <h2 className="ap-asked">{turn.question}</h2>
                {turn.state === "asking" && <Searching startedAt={turn.startedAt} />}
                {turn.state === "failed" && (
                  <div className="ap-trouble">
                    <p>{turn.problem}</p>
                    <button
                      type="button"
                      className="ap-go"
                      disabled={busy}
                      onClick={() => ask(turn.question, turn.id)}
                    >
                      Try again
                    </button>
                  </div>
                )}
                {turn.state === "answered" && turn.reply && (
                  <Answered reply={turn.reply} seconds={turn.seconds ?? 0} />
                )}
              </section>
            </article>
          ))}
        </main>
      )}

      <EventsPanel />

      <form
        ref={form}
        className="ap-bar"
        onSubmit={(event) => {
          event.preventDefault();
          ask(draft);
        }}
      >
        <label className="ap-sr" htmlFor="question">
          Your question
        </label>
        <input
          ref={input}
          id="question"
          className="ap-input"
          value={draft}
          maxLength={MAX_QUESTION}
          autoComplete="off"
          placeholder={started ? "Ask another question" : "Why is it built this way?"}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" className="ap-go" disabled={busy}>
          {busy ? "Asking" : "Ask"}
        </button>
      </form>

      {(!started || leaving) && (
        <div ref={chips} className="ap-chips" data-leaving={leaving || undefined}>
          {EXAMPLE_QUESTIONS.map((question) => (
            <button type="button" key={question} className="ap-chip" onClick={() => ask(question)}>
              {question}
            </button>
          ))}
        </div>
      )}

      <p className="ap-fine">This demo runs on a made-up company&apos;s code, pull requests and Slack.</p>
    </div>
  );
}

function Searching({ startedAt }: { startedAt: number }) {
  const [now, setNow] = useState(startedAt);

  useEffect(() => {
    const timer = setInterval(() => setNow(performance.now()), 100);
    return () => clearInterval(timer);
  }, []);

  return (
    <div role="status">
      <p className="ap-searching">
        Searching the code, pull requests and Slack
        <span className="ap-clock" aria-hidden="true">
          {((now - startedAt) / 1000).toFixed(1)}s
        </span>
      </p>
      <div className="ap-shells" aria-hidden="true">
        {["leaf", "cobalt", "ink", "coral"].map((tone, index) => (
          <i key={tone} className={`ap-shell tone-${tone}`} style={{ "--i": index } as CSSProperties} />
        ))}
      </div>
    </div>
  );
}

function Answered({ reply, seconds }: { reply: Answer; seconds: number }) {
  const words = reply.answer.split(/\s+/);
  const step = Math.min(16, 640 / words.length);
  const size = reply.answer.length <= 170 ? "large" : reply.answer.length <= 320 ? "medium" : "small";
  const stops = inStoryOrder(reply.sources);

  return (
    <>
      <p className="ap-answer" data-size={size}>
        <span className="ap-sr">{reply.answer}</span>
        <span aria-hidden="true">
          {words.map((word, index) => (
            <span key={index}>
              <span className="ap-word">
                <span style={{ "--d": `${index * step}ms` } as CSSProperties}>{word}</span>
              </span>{" "}
            </span>
          ))}
        </span>
      </p>
      <p className="ap-timing">
        {reply.sample ? "Answered" : "Answered live"} in {seconds.toFixed(1)} seconds
        {!reply.sample && reply.meta?.retriever && <span className="ap-sample">via {reply.meta.retriever}</span>}
        {reply.sample && <span className="ap-sample">Sample answer. The real agent isn&apos;t connected yet.</span>}
      </p>
      {stops.length > 0 ? (
        <ul className="ap-srcs" aria-label="Sources">
          {stops.map((source, index) => (
            <SourceCard key={`${source.url}-${index}`} source={source} index={index} />
          ))}
        </ul>
      ) : (
        <p className="ap-unsourced">No sources came back. Check with a person before you act on this.</p>
      )}
    </>
  );
}
