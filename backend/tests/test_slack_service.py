import hashlib
import hmac
import time

from app.services.slack_service import SlackService


def test_verify_signature_success(monkeypatch):
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test_secret")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_INTEGRATION_ENABLED", "true")

    service = SlackService()
    body = b"token=abc&command=%2Fbacklogai"
    timestamp = str(int(time.time()))
    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    digest = hmac.new(b"test_secret", basestring.encode("utf-8"), hashlib.sha256).hexdigest()
    signature = f"v0={digest}"

    assert service.verify_signature(timestamp=timestamp, signature=signature, body=body) is True


def test_verify_signature_rejects_old_timestamp(monkeypatch):
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "test_secret")
    service = SlackService()
    body = b"x=1"
    old_timestamp = str(int(time.time()) - 600)
    basestring = f"v0:{old_timestamp}:{body.decode('utf-8')}"
    digest = hmac.new(b"test_secret", basestring.encode("utf-8"), hashlib.sha256).hexdigest()
    signature = f"v0={digest}"

    assert service.verify_signature(timestamp=old_timestamp, signature=signature, body=body) is False


def test_parse_modal_submission():
    payload = {
        "view": {
            "state": {
                "values": {
                    "context": {
                        "context": {"value": "Local Jira + Slack integration"}
                    },
                    "objective": {
                        "objective": {"value": "Generate and sync stories from Slack"}
                    },
                    "target_user": {
                        "target_user": {"value": "Product Manager"}
                    },
                    "market_segment": {
                        "market_segment": {"value": "B2B SaaS"}
                    },
                    "constraints": {
                        "constraints": {"value": "Keep existing clients unchanged"}
                    },
                    "success_metrics": {
                        "success_metrics": {"value": "Reduce backlog prep time by 30%"}
                    },
                    "competitors": {
                        "competitors": {"value": "Linear, Productboard"}
                    },
                }
            }
        }
    }

    parsed = SlackService.parse_modal_submission(payload)
    assert parsed["context"] == "Local Jira + Slack integration"
    assert parsed["objective"] == "Generate and sync stories from Slack"
    assert parsed["target_user"] == "Product Manager"
    assert parsed["market_segment"] == "B2B SaaS"
    assert parsed["constraints"] == "Keep existing clients unchanged"
    assert parsed["success_metrics"] == "Reduce backlog prep time by 30%"
    assert parsed["competitors_optional"] == ["Linear", "Productboard"]
