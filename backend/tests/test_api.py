from fastapi.testclient import TestClient
from app.main import app
import pytest

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
