from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def test_analytics_health() -> None:
    client = TestClient(app)

    response = client.get("/analytics/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "analytics",
        "event_sink": "d2c_behavior_events",
    }


def test_record_page_view_event() -> None:
    client = TestClient(app)
    anonymous_id = unique_code("anon")
    session_code = unique_code("sess")

    response = client.post(
        "/analytics/events",
        json={
            "anonymous_id": anonymous_id,
            "session_code": session_code,
            "event_type": "page_view",
            "page_path": "/d2c/",
            "metadata": {"source": "test"},
        },
        headers={"User-Agent": "pytest-agent"},
    )

    assert response.status_code == 202

    payload = response.json()
    assert payload["accepted"] is True
    assert payload["event_code"].startswith("EVT-")
    assert payload["session_code"] == session_code
    assert payload["event_type"] == "page_view"


def test_record_product_duration_event_reuses_session() -> None:
    client = TestClient(app)
    anonymous_id = unique_code("anon")
    session_code = unique_code("sess")

    first_response = client.post(
        "/analytics/events",
        json={
            "anonymous_id": anonymous_id,
            "session_code": session_code,
            "event_type": "product_view",
            "page_path": "/d2c/products/pet-cat-food-salmon-001",
            "product_code": "pet-cat-food-salmon-001",
            "sku_code": "CAT-FOOD-SALMON-1KG",
        },
    )

    second_response = client.post(
        "/analytics/events",
        json={
            "anonymous_id": anonymous_id,
            "session_code": session_code,
            "event_type": "product_view_duration",
            "page_path": "/d2c/products/pet-cat-food-salmon-001",
            "product_code": "pet-cat-food-salmon-001",
            "sku_code": "CAT-FOOD-SALMON-1KG",
            "duration_ms": 42000,
            "metadata": {"source": "catalog_card"},
        },
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202
    assert first_response.json()["session_code"] == session_code
    assert second_response.json()["session_code"] == session_code
