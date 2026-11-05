# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""Fire canned events at the agent for the demo.

  uv run triggerware/simulate.py pr-no-why      # merged PR with no "why" -> agent flags it
  uv run triggerware/simulate.py pr-ok          # merged PR with a why -> plain info event
  uv run triggerware/simulate.py alex-left      # same as marking Alex "left" on the /team page
  uv run triggerware/simulate.py sam-joined     # new hire -> onboarding plan
"""

import os
import sys

import httpx

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8008").rstrip("/")
REPO = "https://github.com/aybaris901-integ/wiki-onyx"

EVENTS = {
    "pr-no-why": ("POST", "/events", {
        "type": "pr_merged",
        "payload": {"number": 991, "title": "Bump image cache TTL to 24h", "author": "Alex Chen",
                    "url": f"{REPO}/pulls?q=Bump+image+cache+TTL", "body": "Changes TTL from 1h to 24h."},
    }),
    "pr-ok": ("POST", "/events", {
        "type": "pr_merged",
        "payload": {"number": 992, "title": "Retry queue: cap attempts at 5", "author": "Priya Raman",
                    "url": f"{REPO}/pulls?q=cap+attempts", "body": "## Why\nBecause unbounded retries kept hammering the provider during the Aug outage."},
    }),
    "alex-left": ("POST", "/roster/alex/status", {"status": "left"}),
    "sam-joined": ("POST", "/roster/sam/status", {"status": "new"}),
}


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    if name not in EVENTS:
        print(__doc__)
        sys.exit(1)
    method, path, body = EVENTS[name]
    reply = httpx.request(method, f"{AGENT_URL}{path}", json=body, timeout=30)
    print(reply.status_code, reply.text[:800])


if __name__ == "__main__":
    main()
