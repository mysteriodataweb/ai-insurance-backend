"""End-to-end API tests against a real PostgreSQL database (set TEST_DATABASE_URL). The LLM is faked."""

import os
from datetime import date, timedelta

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.errors import LLMError  # noqa: E402
from app.main import app  # noqa: E402
from app.prompts import EXTRACTION_SYSTEM_PROMPT  # noqa: E402
from app.rate_limit import limiters  # noqa: E402
from app.services import ai_agent, ai_extraction  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()


class FakeLLM:
    def __init__(self):
        self.extraction = {
            "extracted_data": {
                "incident_type": "Car accident",
                "incident_date": YESTERDAY,
                "incident_location": "Casablanca",
                "estimated_amount": 3000,
                "damage_description": "Front bumper damaged",
                "other_party_info": None,
                "policy_number": None,
            },
            "confidence_scores": {"incident_type": 0.9, "incident_date": 0.9, "incident_location": 0.9,
                                  "estimated_amount": 0.8, "damage_description": 0.9},
        }
        self.fail = False
        self.calls = 0

    async def __call__(self, system_prompt, user_content, temperature=0.1):
        self.calls += 1
        if self.fail:
            raise LLMError("AI provider request failed (APITimeoutError).")
        if system_prompt.startswith(EXTRACTION_SYSTEM_PROMPT[:40]):
            return self.extraction
        if '"questions"' in system_prompt:
            return {"questions": ["Could you share your policy number?"]}
        return {"updated_data": {"policy_number": "POL-9"}}


@pytest.fixture
async def llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(ai_extraction, "complete_json", fake)
    monkeypatch.setattr(ai_agent, "complete_json", fake)
    return fake


@pytest.fixture
async def client(llm):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    for limiter in limiters:
        limiter.reset()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def register(client, email="adjuster@example.com", name="Ada Adjuster") -> dict:
    res = await client.post("/api/auth/register", json={"email": email, "full_name": name, "password": "s3cret-pass"})
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def claim_payload(**overrides) -> dict:
    payload = {
        "customer_name": "Ahmed Benali",
        "customer_email": "ahmed@example.com",
        "raw_description": "Another vehicle hit my car at an intersection yesterday in Casablanca.",
        "estimated_amount": 3000,
    }
    payload.update(overrides)
    return payload


async def submit(client, **overrides) -> dict:
    res = await client.post("/api/claims", json=claim_payload(**overrides))
    assert res.status_code == 201, res.text
    return res.json()


async def test_ops_endpoints_require_authentication(client):
    claim = await submit(client)
    for method, path in [
        ("GET", "/api/claims"),
        ("GET", f"/api/claims/{claim['id']}"),
        ("PUT", f"/api/claims/{claim['id']}/action"),
        ("POST", f"/api/agent/extract/{claim['id']}"),
        ("POST", f"/api/risk/assess/{claim['id']}"),
        ("GET", "/api/dashboard/summary"),
        ("GET", "/api/analytics/metrics"),
    ]:
        res = await client.request(method, path)
        assert res.status_code == 401, (method, path)


async def test_login_flow(client):
    await register(client)
    bad = await client.post("/api/auth/login", json={"email": "adjuster@example.com", "password": "nope"})
    assert bad.status_code == 401
    ok = await client.post("/api/auth/login", json={"email": "ADJUSTER@example.com", "password": "s3cret-pass"})
    assert ok.status_code == 200
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {ok.json()['access_token']}"})
    assert me.json()["email"] == "adjuster@example.com"
    dup = await client.post("/api/auth/register", json={"email": "adjuster@example.com", "full_name": "X", "password": "s3cret-pass"})
    assert dup.status_code == 409


async def test_claim_validation(client):
    res = await client.post("/api/claims", json=claim_payload(customer_email="not-an-email", customer_name=""))
    assert res.status_code == 422
    res = await client.post("/api/claims", json=claim_payload(incident_date=(date.today() + timedelta(days=10)).isoformat()))
    assert res.status_code == 422
    res = await client.post("/api/claims", json=claim_payload(policy_number="", incident_date=""))
    assert res.status_code == 201
    assert res.json()["policy_number"] is None


async def test_submission_runs_ai_pipeline_and_audit_trail(client, llm):
    headers = await register(client)
    claim = await submit(client)

    detail = (await client.get(f"/api/claims/{claim['id']}", headers=headers)).json()
    assert detail["status"] == "follow_up"            # policy number is missing
    assert detail["risk_level"] == "low"
    assert detail["incident_type"] == "Car accident"  # filled from the extraction
    assert detail["created_at"].endswith("Z") or detail["created_at"].endswith("+00:00")

    extraction = (await client.get(f"/api/agent/extraction/{claim['id']}", headers=headers)).json()
    assert extraction["missing_fields"] == ["policy_number"]

    conversation = (await client.get(f"/api/agent/conversation/{claim['id']}", headers=headers)).json()
    assert [m["message"] for m in conversation] == ["Could you share your policy number?"]

    events = [e["event_type"] for e in (await client.get(f"/api/claims/{claim['id']}/audit", headers=headers)).json()]
    assert set(events) == {"claim_submitted", "ai_extraction_completed", "risk_assessed", "follow_up_generated"}

    res = await client.post(f"/api/agent/respond/{claim['id']}", json={"message": "My policy is POL-9"}, headers=headers)
    assert res.json() == {"status": "ready_for_review", "still_missing": []}
    detail = (await client.get(f"/api/claims/{claim['id']}", headers=headers)).json()
    assert detail["policy_number"] == "POL-9"
    extraction = (await client.get(f"/api/agent/extraction/{claim['id']}", headers=headers)).json()
    assert extraction["confidence_scores"]["policy_number"] == 1.0

    risk = (await client.post(f"/api/risk/assess/{claim['id']}", headers=headers)).json()
    assert not any("confidence" in s for s in risk["signals"])


async def test_pipeline_failure_is_recorded(client, llm):
    llm.fail = True
    headers = await register(client)
    claim = await submit(client)
    detail = (await client.get(f"/api/claims/{claim['id']}", headers=headers)).json()
    assert detail["status"] == "submitted"
    events = (await client.get(f"/api/claims/{claim['id']}/audit", headers=headers)).json()
    assert events[0]["event_type"] == "ai_pipeline_failed"

    res = await client.post(f"/api/agent/extract/{claim['id']}", headers=headers)
    assert res.status_code == 502
    assert "APITimeoutError" in res.json()["detail"]


async def test_ai_steps_are_idempotent(client, monkeypatch):
    monkeypatch.setattr(settings, "AUTO_PROCESS_CLAIMS", False)
    headers = await register(client)
    claim = await submit(client, policy_number="POL-1")

    res = await client.post(f"/api/risk/assess/{claim['id']}", headers=headers)
    assert res.status_code == 409  # extraction must come first

    for _ in range(2):
        res = await client.post(f"/api/agent/extract/{claim['id']}", headers=headers)
        assert res.status_code == 200, res.text
        res = await client.post(f"/api/risk/assess/{claim['id']}", headers=headers)
        assert res.status_code == 200, res.text

    res = await client.post(f"/api/agent/follow-up/{claim['id']}", headers=headers)
    assert res.json() == {"questions": []}  # nothing missing

    res = await client.post("/api/agent/extract/00000000-0000-0000-0000-000000000000", headers=headers)
    assert res.status_code == 404


async def test_high_risk_requires_escalation_and_four_eyes(client, llm):
    llm.extraction["extracted_data"].update(estimated_amount=18000, policy_number="POL-7",
                                           incident_date=(date.today() - timedelta(days=100)).isoformat())
    adjuster = await register(client)
    manager = await register(client, email="manager@example.com", name="Max Manager")
    claim = await submit(client, estimated_amount=30000)
    claim_id = claim["id"]

    detail = (await client.get(f"/api/claims/{claim_id}", headers=adjuster)).json()
    assert detail["risk_level"] == "high"
    assert detail["status"] == "under_review"

    res = await client.put(f"/api/claims/{claim_id}/action", json={"action": "approved", "notes": "ok"}, headers=adjuster)
    assert res.status_code == 409 and "escalated" in res.json()["detail"]

    res = await client.put(f"/api/claims/{claim_id}/action", json={"action": "escalated"}, headers=adjuster)
    assert res.json()["new_status"] == "escalated"

    res = await client.put(f"/api/claims/{claim_id}/action", json={"action": "approved", "notes": "verified"}, headers=adjuster)
    assert res.status_code == 409 and "Four-eyes" in res.json()["detail"]

    res = await client.put(f"/api/claims/{claim_id}/action", json={"action": "approved"}, headers=manager)
    assert res.status_code == 409 and "justification" in res.json()["detail"]

    res = await client.put(f"/api/claims/{claim_id}/action", json={"action": "approved", "notes": "Receipts verified"}, headers=manager)
    assert res.json()["new_status"] == "approved"

    actions = (await client.get(f"/api/claims/{claim_id}/actions", headers=adjuster)).json()
    assert [a["performed_by"] for a in actions] == ["manager@example.com", "adjuster@example.com"]

    res = await client.post(f"/api/agent/extract/{claim_id}", headers=adjuster)
    assert res.status_code == 409  # closed claims are frozen

    res = await client.put(f"/api/claims/{claim_id}/action", json={"action": "bogus"}, headers=adjuster)
    assert res.status_code == 422


async def test_attachments(client):
    headers = await register(client)
    claim = await submit(client)
    url = f"/api/claims/{claim['id']}/attachments"

    res = await client.post(url, files=[("files", ("photo.png", PNG, "image/png")), ("files", ("../../etc/report.pdf", b"%PDF-1.4 x", "text/plain"))])
    assert res.status_code == 201, res.text
    uploaded = res.json()
    assert [(a["filename"], a["content_type"]) for a in uploaded] == [("photo.png", "image/png"), ("report.pdf", "application/pdf")]

    res = await client.post(url, files=[("files", ("evil.html", b"<script>alert(1)</script>", "image/png"))])
    assert res.status_code == 415

    res = await client.post(url, files=[("files", ("big.png", PNG + b"\x00" * (5 * 1024 * 1024), "image/png"))])
    assert res.status_code == 413

    assert (await client.get(url)).status_code == 401
    listing = (await client.get(url, headers=headers)).json()
    assert len(listing) == 2
    download = await client.get(f"{url}/{listing[0]['id']}", headers=headers)
    assert download.content == PNG
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in download.headers["content-disposition"]


async def test_rate_limit_on_public_submission(client):
    for _ in range(20):
        await submit(client)
    res = await client.post("/api/claims", json=claim_payload())
    assert res.status_code == 429


async def test_real_metrics(client):
    headers = await register(client)
    await submit(client)
    metrics = (await client.get("/api/analytics/metrics", headers=headers)).json()
    assert metrics["total_claims"] == 1
    assert metrics["ai_processed_claims"] == 1
    assert metrics["ai_processed_rate"] == 100.0
    assert metrics["by_type"] == [{"name": "Car accident", "count": 1}]
    assert metrics["claims_per_day"][-1]["count"] == 1
    assert sum(w["count"] for w in metrics["claims_per_week"]) == 1
    assert metrics["avg_decision_hours"] is None
    assert "avg_processing_time_before" not in metrics
