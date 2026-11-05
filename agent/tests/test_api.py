import json
import time


def test_health(client):
    data = client.get("/health").json()
    assert data["ok"] and data["docs"] > 5 and data["llm"] == "extractive" and data["vectors"] is True


def test_ask_round_trip(client):
    response = client.post("/ask", json={"question": "Why do payments go through a queue?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] and isinstance(data["sources"], list)
    assert {"type", "url", "author", "date"} <= set(data["sources"][0])
    assert data["meta"]["live"] is True


def test_ask_rejects_empty(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_rate_limit(settings, brain):
    from fastapi.testclient import TestClient

    from brain.app import create_app

    settings.rate_limit_per_minute = 2
    with TestClient(create_app(settings, brain)) as client:
        assert client.post("/ask", json={"question": "a"}).status_code == 200
        assert client.post("/ask", json={"question": "b"}).status_code == 200
        assert client.post("/ask", json={"question": "c"}).status_code == 429


def test_webhook_pr_missing_why(client):
    response = client.post("/events", json={"type": "pr_merged", "payload": {"number": 9, "title": "Bump TTL", "author": "Alex Chen", "body": "Bump."}})
    assert response.status_code == 200
    types = [e["type"] for e in client.get("/events").json()["events"]]
    assert types[:2] == ["pr_missing_why", "pr_merged"]


def test_mark_alex_left_emits_handoff(client):
    response = client.post("/roster/alex/status", json={"status": "left"})
    assert response.status_code == 200
    body = response.json()
    assert body["person"]["status"] == "left" and body["person"]["left"]
    assert body["events"][0]["type"] == "employee_left"
    deadline = time.time() + 5
    report = None
    while time.time() < deadline and report is None:
        events = client.get("/events").json()["events"]
        report = next((e for e in events if e["type"] == "handoff_report"), None)
        time.sleep(0.05)
    assert report, "handoff report never arrived"
    assert "## What they owned" in report["body"] and "## Who takes over" in report["body"]
    assert "services/images/" in report["body"]
    assert "Dana Whitlock" in report["body"] and "Priya Raman" in report["body"]
    assert report["sources"] and report["severity"] == "good"
    # roster file was rewritten
    assert "Alex Chen,alex" in (client.app.state.brain.roster.path).read_text()
    assert "left" in [p["status"] for p in client.get("/roster").json()["people"] if p["handle"] == "alex"]


def test_new_hire_emits_onboarding_plan(client):
    client.post("/roster/sam/status", json={"status": "new"})
    deadline = time.time() + 5
    plan = None
    while time.time() < deadline and plan is None:
        plan = next((e for e in client.get("/events").json()["events"] if e["type"] == "onboarding_plan"), None)
        time.sleep(0.05)
    assert plan and "## Week 1" in plan["body"]


def test_roster_reset_reloads_and_clears(client):
    client.post("/roster/alex/status", json={"status": "left"})
    data = client.post("/roster/reset").json()
    assert client.get("/events").json()["events"] == []
    assert "Alex Chen,alex,alex@acme.example,Senior Engineer,Media,active" in client.app.state.brain.roster.path.read_text()
    assert any(p["handle"] == "alex" for p in data["people"])


def test_unknown_person_404(client):
    assert client.post("/roster/nobody/status", json={"status": "left"}).status_code == 404


def test_sse_stream_yields_event(client):
    with client.stream("GET", "/events/stream") as stream:
        client.post("/events", json={"type": "info", "payload": {"title": "ping"}})
        for line in stream.iter_lines():
            if line.startswith("data:"):
                event = json.loads(line[5:])
                assert event["title"] == "ping"
                break
