from app.services.jira_service import JiraService


def test_normalize_jira_url_keeps_regular_host():
    raw = "http://localhost:8081"
    assert JiraService._normalize_jira_url(raw) == raw


def test_normalize_jira_url_rewrites_unresolvable_docker_alias(monkeypatch):
    def _raise(_host):
        raise OSError("unresolvable")

    monkeypatch.setattr("socket.gethostbyname", _raise)

    raw = "http://host.docker.internal:8081"
    assert JiraService._normalize_jira_url(raw) == "http://localhost:8081"


def test_normalize_jira_url_keeps_resolvable_docker_alias(monkeypatch):
    monkeypatch.setattr("socket.gethostbyname", lambda _host: "127.0.0.1")

    raw = "http://host.docker.internal:8081"
    assert JiraService._normalize_jira_url(raw) == raw


def test_map_priority_name_from_priority_band_labels():
    assert JiraService._map_priority_name("Very High") == "Highest"
    assert JiraService._map_priority_name("High") == "High"
    assert JiraService._map_priority_name("Medium") == "Medium"
    assert JiraService._map_priority_name("Low") == "Low"
