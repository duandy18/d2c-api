from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16].upper()}"


def promotion_payload(promotion_code: str | None = None) -> dict[str, object]:
    return {
        "promotion_code": promotion_code or unique_code("BACKOFFICEPROMO"),
        "name": "后台测试全店促销",
        "description": "backoffice promotion management test",
        "promotion_type": "store_campaign",
        "discount_type": "percentage",
        "discount_value": 10,
        "scope_type": "all_store",
        "min_order_amount_cents": None,
        "max_discount_cents": None,
        "currency": "USD",
        "starts_at": None,
        "ends_at": None,
        "priority": 10,
        "stackable": False,
    }


def test_backoffice_promotions_requires_backoffice_client(client: TestClient) -> None:
    response = client.get("/backoffice/promotions")

    assert response.status_code == 401
    assert response.json() == {"detail": "backoffice_client_required"}


def test_backoffice_promotions_health(client: TestClient) -> None:
    response = client.get("/backoffice/promotions/health", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "backoffice_promotions",
        "surface": "merchant_management",
    }


def test_backoffice_promotions_create_returns_draft_promotion(client: TestClient) -> None:
    payload = promotion_payload()

    response = client.post(
        "/backoffice/promotions",
        json=payload,
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 201

    body = response.json()
    assert body["promotion_code"] == payload["promotion_code"]
    assert body["status"] == "draft"
    assert body["is_active"] is False
    assert body["promotion_type"] == "store_campaign"
    assert body["discount_type"] == "percentage"
    assert body["discount_value"] == 10
    assert body["scope_type"] == "all_store"


def test_backoffice_promotions_create_rejects_duplicate_code(client: TestClient) -> None:
    code = unique_code("DUPBACKOFFICEPROMO")
    payload = promotion_payload(code)

    first_response = client.post(
        "/backoffice/promotions",
        json=payload,
        headers=BACKOFFICE_HEADERS,
    )
    second_response = client.post(
        "/backoffice/promotions",
        json=payload,
        headers=BACKOFFICE_HEADERS,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "promotion_code_already_exists"}


def test_backoffice_promotions_activate_and_deactivate(client: TestClient) -> None:
    create_response = client.post(
        "/backoffice/promotions",
        json=promotion_payload(),
        headers=BACKOFFICE_HEADERS,
    )
    promotion_code = create_response.json()["promotion_code"]

    activate_response = client.post(
        f"/backoffice/promotions/{promotion_code}/activate",
        headers=BACKOFFICE_HEADERS,
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["promotion_code"] == promotion_code
    assert activate_response.json()["status"] == "active"
    assert activate_response.json()["is_active"] is True

    deactivate_response = client.post(
        f"/backoffice/promotions/{promotion_code}/deactivate",
        headers=BACKOFFICE_HEADERS,
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["promotion_code"] == promotion_code
    assert deactivate_response.json()["status"] == "paused"
    assert deactivate_response.json()["is_active"] is False


def test_backoffice_promotions_activate_returns_404_for_unknown_code(
    client: TestClient,
) -> None:
    response = client.post(
        "/backoffice/promotions/UNKNOWN-PROMO/activate",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "promotion_not_found"}


def test_backoffice_promotions_list_includes_created_promotion(client: TestClient) -> None:
    create_response = client.post(
        "/backoffice/promotions",
        json=promotion_payload(),
        headers=BACKOFFICE_HEADERS,
    )
    promotion_code = create_response.json()["promotion_code"]

    response = client.get("/backoffice/promotions", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] >= 1
    promotion_by_code = {
        promotion["promotion_code"]: promotion for promotion in payload["promotions"]
    }

    assert promotion_code in promotion_by_code


def test_backoffice_promotion_targets_list_includes_created_all_store_target(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/backoffice/promotions",
        json=promotion_payload(),
        headers=BACKOFFICE_HEADERS,
    )
    promotion_code = create_response.json()["promotion_code"]

    response = client.get("/backoffice/promotions/targets", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    targets = [
        target
        for target in response.json()["promotion_targets"]
        if target["promotion_code"] == promotion_code
    ]

    assert targets
    assert targets[0]["target_type"] == "all_store"


def test_backoffice_coupons_returns_list(client: TestClient) -> None:
    response = client.get("/backoffice/promotions/coupons", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200
    assert "count" in response.json()
    assert "coupons" in response.json()


def test_backoffice_customer_coupons_returns_list(client: TestClient) -> None:
    response = client.get("/backoffice/promotions/customer-coupons", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200
    assert "count" in response.json()
    assert "customer_coupons" in response.json()
