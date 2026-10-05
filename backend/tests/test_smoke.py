"""M0 smoke test: the app imports and answers its health check."""

from fastapi.testclient import TestClient

from seedfoundry.main import app


def test_health_answers_ok():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "SeedFactory"}
