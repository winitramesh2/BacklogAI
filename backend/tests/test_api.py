from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_generate_backlog_item():
    payload = {
        "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "title": "Test Feature",
        "description": "Implement a test feature.",
        "personas": ["Tester"],
        "pillar_scores": {
            "user_value": 8.0,
            "commercial_impact": 8.0,
            "strategic_horizon": 5.0,
            "competitive_positioning": 5.0,
            "technical_reality": 5.0
        }
    }
    
    response = client.post("/backlog/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Feature"
    assert data["priority_score"] >= 60.0
    assert "acceptance_criteria" in data


class _DummySlackService:
    def __init__(self):
        self.is_configured = True
        self.modal_opened = False

    def verify_signature(self, timestamp, signature, body):
        return True

    async def open_input_modal(self, trigger_id, channel_id, user_id):
        self.modal_opened = True


def test_slack_commands_opens_modal(monkeypatch):
    dummy = _DummySlackService()
    monkeypatch.setattr(main_module, "slack_service", dummy)

    response = client.post(
        "/slack/commands",
        data={
            "command": "/backlogai",
            "trigger_id": "12345.abcde",
            "channel_id": "C123",
            "user_id": "U123",
        },
        headers={
            "x-slack-signature": "v0=dummy",
            "x-slack-request-timestamp": "123",
        },
    )

    assert response.status_code == 200
    assert response.json()["response_type"] == "ephemeral"
    assert dummy.modal_opened is True


def test_slack_events_url_verification(monkeypatch):
    dummy = _DummySlackService()
    monkeypatch.setattr(main_module, "slack_service", dummy)

    payload = {"type": "url_verification", "challenge": "challenge-token"}
    response = client.post(
        "/slack/events",
        json=payload,
        headers={
            "x-slack-signature": "v0=dummy",
            "x-slack-request-timestamp": "123",
        },
    )

    assert response.status_code == 200
    assert response.json()["challenge"] == "challenge-token"


def test_slack_interactions_missing_payload(monkeypatch):
    dummy = _DummySlackService()
    monkeypatch.setattr(main_module, "slack_service", dummy)

    response = client.post(
        "/slack/interactions",
        data={},
        headers={
            "x-slack-signature": "v0=dummy",
            "x-slack-request-timestamp": "123",
        },
    )

    assert response.status_code == 400
