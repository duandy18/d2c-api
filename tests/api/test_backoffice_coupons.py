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
        "promotion_code": promotion_code or unique_code("COUPONPROMO"),
        "name": "优惠券测试促销",
        "description": "coupon management promotion",
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


def coupon_payload(coupon_code: str | None = None) -> dict[str, object]:
    return {
        "coupon_code": coupon_code or unique_code("COUPON"),
        "name": "测试优惠券",
        "coupon_type": "public_code",
        "total_limit": 100,
        "per_customer_limit": 1,
        "starts_at": None,
        "ends_at": None,
    }


def create_promotion(client: TestClient) -> str:
    response = client.post(
        "/backoffice/promotions",
        json=promotion_payload(),
        headers=BACKOFFICE_HEADERS,
    )
    assert response.status_code == 201
    return response.json()["promotion_code"]


def create_coupon(client: TestClient, promotion_code: str, coupon_code: str | None = None) -> str:
    response = client.post(
        f"/backoffice/promotions/{promotion_code}/coupons",
        json=coupon_payload(coupon_code),
        headers=BACKOFFICE_HEADERS,
    )
    assert response.status_code == 201
    return response.json()["coupon_code"]


def test_backoffice_coupon_create_requires_backoffice_client(client: TestClient) -> None:
    promotion_code = create_promotion(client)

    response = client.post(
        f"/backoffice/promotions/{promotion_code}/coupons",
        json=coupon_payload(),
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "backoffice_client_required"}


def test_backoffice_coupon_create_returns_draft_coupon(client: TestClient) -> None:
    promotion_code = create_promotion(client)
    payload = coupon_payload()

    response = client.post(
        f"/backoffice/promotions/{promotion_code}/coupons",
        json=payload,
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 201

    body = response.json()
    assert body["coupon_code"] == payload["coupon_code"]
    assert body["name"] == payload["name"]
    assert body["promotion_code"] == promotion_code
    assert body["coupon_type"] == "public_code"
    assert body["total_limit"] == 100
    assert body["per_customer_limit"] == 1
    assert body["status"] == "draft"
    assert body["is_active"] is False


def test_backoffice_coupon_create_rejects_unknown_promotion(client: TestClient) -> None:
    response = client.post(
        "/backoffice/promotions/UNKNOWN-PROMO/coupons",
        json=coupon_payload(),
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "promotion_not_found"}


def test_backoffice_coupon_create_rejects_duplicate_code(client: TestClient) -> None:
    promotion_code = create_promotion(client)
    coupon_code = unique_code("DUPCOUPON")

    first_response = client.post(
        f"/backoffice/promotions/{promotion_code}/coupons",
        json=coupon_payload(coupon_code),
        headers=BACKOFFICE_HEADERS,
    )
    second_response = client.post(
        f"/backoffice/promotions/{promotion_code}/coupons",
        json=coupon_payload(coupon_code),
        headers=BACKOFFICE_HEADERS,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "coupon_code_already_exists"}


def test_backoffice_coupon_activate_and_deactivate(client: TestClient) -> None:
    promotion_code = create_promotion(client)
    coupon_code = create_coupon(client, promotion_code)

    activate_response = client.post(
        f"/backoffice/promotions/coupons/{coupon_code}/activate",
        headers=BACKOFFICE_HEADERS,
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["coupon_code"] == coupon_code
    assert activate_response.json()["promotion_code"] == promotion_code
    assert activate_response.json()["status"] == "active"
    assert activate_response.json()["is_active"] is True

    deactivate_response = client.post(
        f"/backoffice/promotions/coupons/{coupon_code}/deactivate",
        headers=BACKOFFICE_HEADERS,
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["coupon_code"] == coupon_code
    assert deactivate_response.json()["status"] == "paused"
    assert deactivate_response.json()["is_active"] is False


def test_backoffice_coupon_activate_returns_404_for_unknown_code(client: TestClient) -> None:
    response = client.post(
        "/backoffice/promotions/coupons/UNKNOWN-COUPON/activate",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "coupon_not_found"}


def test_backoffice_coupon_list_includes_created_coupon(client: TestClient) -> None:
    promotion_code = create_promotion(client)
    coupon_code = create_coupon(client, promotion_code)

    response = client.get(
        "/backoffice/promotions/coupons",
        headers=BACKOFFICE_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] >= 1

    coupon_by_code = {coupon["coupon_code"]: coupon for coupon in payload["coupons"]}
    coupon = coupon_by_code[coupon_code]

    assert coupon["promotion_code"] == promotion_code
    assert coupon["coupon_type"] == "public_code"
