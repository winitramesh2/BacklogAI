from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module
import json

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


class _DummySession:
    def __init__(self, status, preview_payload=None):
        self.status = status
        self.slack_channel_id = "C123"
        self.jira_key = "TAC-1"
        self.jira_url = "http://localhost:8081/browse/TAC-1"
        self.preview_payload = preview_payload or {}


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


def test_slack_interactions_sync_already_synced(monkeypatch):
    class _SlackServiceForSync(_DummySlackService):
        async def get_session(self, session_id):
            return _DummySession(status=main_module.SlackSessionStatus.SYNCED)

        async def post_sync_success(self, channel_id, jira_key, jira_url):
            return {"ok": True}

    dummy = _SlackServiceForSync()
    monkeypatch.setattr(main_module, "slack_service", dummy)

    payload = {
        "type": "block_actions",
        "actions": [{"action_id": "sync_to_jira", "value": "session-1"}],
    }
    response = client.post(
        "/slack/interactions",
        data={"payload": json.dumps(payload)},
        headers={
            "x-slack-signature": "v0=dummy",
            "x-slack-request-timestamp": "123",
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Already synced."


def test_slack_interactions_sync_new_session(monkeypatch):
    class _SlackServiceForSync(_DummySlackService):
        def __init__(self):
            super().__init__()
            self.synced = False

        async def get_session(self, session_id):
            preview = {
                "summary": "Story from Slack",
                "description": "Generated story description",
                "priority": "Should Have",
                "labels": [],
                "components": [],
            }
            return _DummySession(status=main_module.SlackSessionStatus.GENERATED, preview_payload=preview)

        async def mark_synced(self, session, jira_key, jira_url):
            self.synced = True
            session.status = main_module.SlackSessionStatus.SYNCED
            session.jira_key = jira_key
            session.jira_url = jira_url

        async def post_sync_success(self, channel_id, jira_key, jira_url):
            return {"ok": True}

    class _DummyJiraService:
        def create_issue_v2(self, summary, description, priority, issue_type, labels, components):
            return {"key": "TAC-999", "url": "http://localhost:8081/browse/TAC-999"}

    dummy = _SlackServiceForSync()
    monkeypatch.setattr(main_module, "slack_service", dummy)
    monkeypatch.setattr(main_module, "jira_service", _DummyJiraService())

    payload = {
        "type": "block_actions",
        "actions": [{"action_id": "sync_to_jira", "value": "session-2"}],
    }
    response = client.post(
        "/slack/interactions",
        data={"payload": json.dumps(payload)},
        headers={
            "x-slack-signature": "v0=dummy",
            "x-slack-request-timestamp": "123",
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Synced to JIRA."
    assert dummy.synced is True
