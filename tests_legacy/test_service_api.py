from __future__ import annotations

from fastapi.testclient import TestClient

from service.app import app


def test_orchestrate_endpoint():
    client = TestClient(app)
    resp = client.post(
        "/orchestrate",
        json={
            "intent": "service-test",
            "query": "hello",
            "estimated_cost_usd": 1.0,
            "cap_usd": 5.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stop_now"] is False
