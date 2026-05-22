from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def test_backoffice_pages_routes_are_retired() -> None:
    client = TestClient(app)

    for path in (
        "/backoffice/pages/health",
        "/backoffice/pages/registry",
        "/backoffice/pages/navigation",
    ):
        response = client.get(path, headers=BACKOFFICE_HEADERS)
        assert response.status_code == 404
