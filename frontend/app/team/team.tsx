"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { readPerson, type Person, type PersonStatus } from "@/lib/events";
import { readableDate } from "../app/sources";

// The demo control room. Mark someone as left and the brain writes their handoff report.

type Row = Person & { arming?: boolean; working?: boolean; done?: PersonStatus; problem?: string };

const STATUS_LABEL: Record<PersonStatus, string> = { active: "Active", left: "Left", new: "New hire" };

export function Team() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [sample, setSample] = useState(false);
  const [problem, setProblem] = useState("");
  const [resetting, setResetting] = useState(false);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/roster", { cache: "no-store" });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.error ?? "The roster didn't load.");
      const people = (Array.isArray(data?.people) ? data.people : []).map(readPerson).filter((p: Person | null): p is Person => p !== null);
      setRows(people);
      setSample(data?.sample === true);
      setProblem("");
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "The roster didn't load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const patch = (handle: string, change: Partial<Row>) =>
    setRows((all) => all.map((row) => (row.handle === handle ? { ...row, ...change } : row)));

  async function setStatus(row: Row, status: PersonStatus) {
    patch(row.handle, { arming: false, working: true, problem: undefined });
    try {
      const response = await fetch(`/api/roster/${encodeURIComponent(row.handle)}/status`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ status }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.error ?? "The change didn't go through.");
      const person = readPerson(data?.person);
      patch(row.handle, { ...(person ?? {}), working: false, done: status });
      if (data?.sample) setSample(true);
    } catch (error) {
      patch(row.handle, { working: false, problem: error instanceof Error ? error.message : "The change didn't go through." });
    }
  }

  async function reset() {
    setResetting(true);
    try {
      await fetch("/api/roster/reset", { method: "POST" });
      await load();
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="tm">
      <header className="ap-top">
        <Link className="ap-mark" href="/">
          Company Brain
        </Link>
        <nav className="ap-nav" aria-label="Pages">
          <Link className="ap-mark ap-over" href="/app">
            Ask the brain
          </Link>
        </nav>
      </header>

      <main className="tm-main">
        <div className="tm-head">
          <div>
            <h1 className="tm-title">Team</h1>
            <p className="tm-lede">
              Mark someone as left and the brain writes their handoff report from their pull requests, Slack threads and the
              systems they own. Watch it land in <Link href="/app">Live events</Link>.
            </p>
          </div>
          <button type="button" className="ap-chip tm-reset" disabled={resetting} onClick={reset}>
            {resetting ? "Resetting" : "Reset demo"}
          </button>
        </div>

        {sample && <p className="tm-note">Sample roster. The real agent isn&apos;t connected yet.</p>}
        {problem && <p className="tm-problem">{problem}</p>}

        {loading ? (
          <p className="tm-note">Loading the roster</p>
        ) : (
          <div className="tm-table-wrap">
            <table className="tm-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Role</th>
                  <th scope="col">Team</th>
                  <th scope="col">Status</th>
                  <th scope="col">Dates</th>
                  <th scope="col">
                    <span className="ap-sr">Action</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.handle} data-status={row.status}>
                    <td>
                      <strong className="tm-name">{row.name}</strong>
                      <span className="tm-handle">@{row.handle}</span>
                    </td>
                    <td>{row.role}</td>
                    <td>{row.team}</td>
                    <td>
                      <span className={`tm-pill tm-pill-${row.status}`}>{STATUS_LABEL[row.status]}</span>
                    </td>
                    <td className="tm-dates">
                      {row.started && <span>Started {readableDate(row.started)}</span>}
                      {row.left && <span>Left {readableDate(row.left)}</span>}
                    </td>
                    <td className="tm-action">
                      <Action row={row} onArm={() => patch(row.handle, { arming: true })} onCancel={() => patch(row.handle, { arming: false })} onGo={setStatus} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

function Action({
  row,
  onArm,
  onCancel,
  onGo,
}: {
  row: Row;
  onArm: () => void;
  onCancel: () => void;
  onGo: (row: Row, status: PersonStatus) => void;
}) {
  if (row.working) return <span className="tm-wait">Saving</span>;
  if (row.problem) {
    return (
      <span className="tm-problem-inline">
        {row.problem}{" "}
        <button type="button" className="tm-link" onClick={onArm}>
          Try again
        </button>
      </span>
    );
  }
  if (row.done === "left") {
    return (
      <span className="tm-watch">
        <i className="ap-dot ap-dot-live" aria-hidden="true" />
        Watching for the handoff report… <Link href="/app">Open Live events</Link>
      </span>
    );
  }
  if (row.done === "new") {
    return (
      <span className="tm-watch">
        <i className="ap-dot ap-dot-live" aria-hidden="true" />
        Writing the onboarding plan… <Link href="/app">Open Live events</Link>
      </span>
    );
  }
  if (row.arming) {
    return (
      <span className="tm-confirm">
        <button type="button" className="ap-go tm-go tm-danger" onClick={() => onGo(row, "left")}>
          Yes, {row.name.split(" ")[0]} left
        </button>
        <button type="button" className="tm-link" onClick={onCancel}>
          Cancel
        </button>
      </span>
    );
  }
  if (row.status === "left") {
    return (
      <button type="button" className="tm-link" onClick={() => onGo(row, "active")}>
        Mark as active
      </button>
    );
  }
  if (row.status === "new") {
    return (
      <span className="tm-confirm">
        <button type="button" className="ap-go tm-go" onClick={() => onGo(row, "new")}>
          Onboarding plan
        </button>
        <button type="button" className="tm-link" onClick={onArm}>
          Mark as left
        </button>
      </span>
    );
  }
  return (
    <button type="button" className="ap-go tm-go" onClick={onArm}>
      Mark as left
    </button>
  );
}
