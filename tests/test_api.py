import pytest


def test_api_health_and_retro():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")  # required by starlette's TestClient
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"

    tools = client.get("/api/tools").json()["tools"]
    assert any(t["name"] == "synthesize_retro" for t in tools)

    r = client.post("/api/retro", json={"period": "2026-W41", "connectors": ["mock_oa"]})
    assert r.status_code == 200
    body = r.json()
    assert body["period"] == "2026-W41"
    assert any("timeout" in i.lower() for i in body["issues"])
