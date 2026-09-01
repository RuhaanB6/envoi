"""
pytest + httpx smoke test for GET /api/health.

Uses FastAPI's TestClient (built on httpx) as a context manager so the
app's lifespan runs -- that's what opens the real psycopg ConnectionPool.
This is an integration test, not a mock: DATABASE_URL must point at a
running, migrated database (see README.md).
"""

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok_and_real_versions():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert "PostgreSQL" in body["postgres_version"]
    assert body["python_version"]
    assert body["fastapi_version"]
