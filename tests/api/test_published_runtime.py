from fastapi.testclient import TestClient

from app.main import app

SERVICE_HEADERS = {"X-Service-Client": "d2c-service"}


def test_published_routes_require_service_client() -> None:
    client = TestClient(app)

    response = client.get("/published/coupons")

    assert response.status_code == 401
    assert response.json() == {"detail": "service_client_required"}


def test_published_health() -> None:
    client = TestClient(app)

    response = client.get("/published/health", headers=SERVICE_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "published",
        "storage": "d2c_published_runtime_model",
    }


def test_published_empty_lists_are_stable() -> None:
    client = TestClient(app)

    expected_paths = {
        "/published/coupons": "coupons",
        "/published/sync-runs": "sync_runs",
    }

    for path, list_key in expected_paths.items():
        response = client.get(path, headers=SERVICE_HEADERS)

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] >= 0
        assert list_key in payload


def test_legacy_published_catalog_routes_are_retired() -> None:
    client = TestClient(app)

    for path in ("/published/products", "/published/skus", "/published/prices"):
        response = client.get(path, headers=SERVICE_HEADERS)
        assert response.status_code == 404
