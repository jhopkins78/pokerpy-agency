import pytest
import json
from flask import Flask
from src.routes.chat_routes import chat_bp

@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(chat_bp)
    app.testing = True
    return app.test_client()

def test_minimal_payload(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert "response" in data

def test_full_valid_payload(client):
    payload = {
        "user_id": "test_user",
        "message": "How should I play AK suited?",
        "context": {
            "intent": "coaching",
            "emotional_state": "focused",
            "category": "strategy"
        }
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    for key in ["response", "sources", "suggested_simulation", "active_goals", "context_used"]:
        assert key in data

def test_malformed_payload(client):
    response = client.post("/api/chat", data="{ not_json }", content_type='application/json')
    assert response.status_code == 400

def test_missing_context_keys(client):
    payload = {
        "user_id": "test_user",
        "message": "Bluffing advice?",
        "context": {}
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "response" in data
    assert isinstance(data.get("context_used", {}), dict)

def test_agent_health_response_format(client):
    payload = {
        "user_id": "test_health",
        "message": "Trigger simulation test",
        "context": {
            "intent": "simulation",
            "emotional_state": "neutral",
            "category": "practice"
        }
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "suggested_simulation" in data
