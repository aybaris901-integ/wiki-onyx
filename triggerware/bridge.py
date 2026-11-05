# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "pyyaml>=6"]
# ///
"""Bridge between Triggerware and the Company Brain agent.

Run:  uv run triggerware/bridge.py            (from the repo root)

Two modes, chosen automatically:

1. Triggerware mode. If the `triggerware` Python SDK is importable and a server answers at
   TRIGGERWARE_ADDR (default localhost:5221), the bridge creates the triggers in triggers.yaml and
   watches them. Every delta (added rows) becomes a POST /events to the agent.

2. Local mode (no server). The bridge watches ../demo-data/team-roster.csv itself and polls GitHub
   for merged PRs with `gh`. Same events, same webhook. This is the fallback the team agreed on for the
   7:15 PM checkpoint, so the demo never depends on a service that isn't up.

Either way the agent decides what to do with the event: employee_left -> handoff report,
new_hire -> onboarding plan, pr_merged -> flag it when the body has no "why".
"""

from __future__ import annotations

import asyncio
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import yaml

HERE = Path(__file__).resolve().parent
AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8008").rstrip("/")
TW_ADDR = os.environ.get("TRIGGERWARE_ADDR", "localhost:5221")
POLL_SECONDS = float(os.environ.get("BRIDGE_POLL_SECONDS", "2"))


def load_config() -> dict[str, Any]:
    return yaml.safe_load((HERE / "triggers.yaml").read_text())


def render(template: str, row: dict[str, Any]) -> str:
    try:
        return template.format(**{k: ("" if v is None else v) for k, v in row.items()})
    except (KeyError, IndexError):
        return template


async def emit(client: httpx.AsyncClient, trigger: dict[str, Any], row: dict[str, Any]) -> None:
    spec = trigger["emit"]
    event = {
        "type": spec["type"],
        "payload": {
            **row,
            "title": render(spec.get("title", trigger["name"]), row),
            "person": render(spec.get("person", ""), row),
            "severity": spec.get("severity", "info"),
            "trigger": trigger["name"],
        },
    }
    try:
        reply = await client.post(f"{AGENT_URL}/events", json=event, timeout=10)
        print(f"-> {spec['type']}: {event['payload']['title']}  [{reply.status_code}]", flush=True)
    except httpx.HTTPError as error:
        print(f"!! could not reach agent at {AGENT_URL}: {error}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------- Triggerware mode


async def run_triggerware(config: dict[str, Any]) -> bool:
    try:
        from triggerware import TriggerwareClient  # type: ignore[import-not-found]
    except ImportError:
        return False
    try:
        tw = await TriggerwareClient.connect_tcp(TW_ADDR)
    except Exception as error:  # noqa: BLE001 - any failure means "server not up"
        print(f"Triggerware not reachable at {TW_ADDR} ({error}); using local mode.", flush=True)
        return False

    print(f"Connected to Triggerware at {TW_ADDR}", flush=True)
    async with httpx.AsyncClient() as client:
        for trigger in config["triggers"]:
            try:
                await tw.triggers.create(
                    trigger["name"], description=trigger.get("description"), sql=trigger.get("sql"), enabled=True
                )
            except Exception as error:  # noqa: BLE001 - already exists is fine
                print(f"   trigger {trigger['name']}: {error}", flush=True)

            def make_callback(spec: dict[str, Any]):
                async def callback(delta: Any) -> None:
                    added = getattr(delta, "added", None) or (delta.get("added") if isinstance(delta, dict) else [])
                    columns = getattr(delta, "columns", None) or (delta.get("columns") if isinstance(delta, dict) else None)
                    for row in added or []:
                        record = dict(zip(columns, row)) if columns and not isinstance(row, dict) else dict(row)
                        await emit(client, spec, record)

                return callback

            await tw.triggers.watch(trigger["name"], make_callback(trigger))
            print(f"   watching {trigger['name']}", flush=True)
        while True:
            await asyncio.sleep(3600)


# ---------------------------------------------------------------- Local mode


def read_roster(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as handle:
        return {row["handle"]: row for row in csv.DictReader(handle)}


def merged_prs(repo: str) -> dict[int, dict[str, Any]]:
    try:
        out = subprocess.run(
            ["gh", "pr", "list", "-R", repo, "--state", "merged", "--limit", "30",
             "--json", "number,title,body,author,url,mergedAt"],
            check=True, capture_output=True, text=True, timeout=20,
        ).stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return {}
    prs = {}
    for pr in json.loads(out or "[]"):
        prs[pr["number"]] = {
            "number": pr["number"], "title": pr["title"], "body": pr.get("body") or "",
            "author": (pr.get("author") or {}).get("login", ""), "url": pr["url"], "merged_at": pr.get("mergedAt"),
        }
    return prs


async def run_local(config: dict[str, Any]) -> None:
    roster_path = (HERE / config["sources"]["roster"]["path"]).resolve()
    repo = config["sources"]["github"]["repo"]
    by_name = {t["name"]: t for t in config["triggers"]}
    print(f"Local mode: watching {roster_path} and merged PRs on {repo}; posting to {AGENT_URL}", flush=True)

    seen_roster = read_roster(roster_path)
    seen_prs = set(merged_prs(repo))  # don't replay history on start
    gh_tick = 0
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(POLL_SECONDS)
            roster = read_roster(roster_path)
            for handle, row in roster.items():
                before = seen_roster.get(handle, {}).get("status")
                if row.get("status") == "left" and before != "left":
                    await emit(client, by_name["employee_left"], row)
                if row.get("status") == "new" and before not in ("new",) and handle not in seen_roster:
                    await emit(client, by_name["new_hire"], row)
            seen_roster = roster

            gh_tick += 1
            if gh_tick % max(1, int(15 / POLL_SECONDS)) == 0:  # GitHub every ~15 s
                for number, pr in merged_prs(repo).items():
                    if number not in seen_prs:
                        seen_prs.add(number)
                        await emit(client, by_name["pr_merged"], pr)


async def main() -> None:
    config = load_config()
    if not await run_triggerware(config):
        await run_local(config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
