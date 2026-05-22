from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

ADMIN_HEADERS = {"X-Admin-Client": "d2c-admin"}


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16].upper()}"


def unique_email() -> str:
    return f"admin-promo-flow-{uuid4().hex}@example.com"


def unique_phone() -> str:
    return f"177{uuid4().hex[:8]}"


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def register_customer(client: TestClient) -> str:
    response = client.post(
        "/customers/register",
        json={
            "email": unique_email(),
            "password": "StrongPass123",
            "display_name": "Promo Flow Customer",
            "phone": unique_phone(),
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def cart_identity() -> dict[str, str]:
    return {
        "anonymous_id": unique_code("anon"),
        "session_code": unique_code("sess"),
    }


def create_cart_with_item(client: TestClient) -> str:
    identity = cart_identity()
    response = client.post(
        "/cart/items",
        json={
            **identity,
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
            "quantity": 2,
        },
    )
    assert response.status_code == 200
    return response.json()["cart_code"]


def checkout_payload(cart_code: str) -> dict[str, str]:
    return {
        "cart_code": cart_code,
        "recipient_name": "Andy",
        "recipient_phone": "18800001111",
        "shipping_country": "US",
        "shipping_province": "CA",
        "shipping_city": "Los Angeles",
        "shipping_district": "LA",
        "shipping_address_line1": "100 Test Street",
        "shipping_address_line2": "Unit 1",
        "shipping_postal_code": "90001",
        "payment_provider": "mock",
        "payment_method": "mock",
    }


def create_admin_promotion(client: TestClient) -> str:
    promotion_code = unique_code("FLOWPROMO")
    response = client.post(
        "/admin/promotions",
        json={
            "promotion_code": promotion_code,
            "name": "后台创建后前台执行测试",
            "description": "admin creates, checkout executes",
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
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 201
    return promotion_code


def test_admin_created_active_promotion_is_applied_then_deactivated() -> None:
    client = TestClient(app)
    promotion_code = create_admin_promotion(client)

    token = register_customer(client)
    draft_cart_code = create_cart_with_item(client)

    draft_checkout_response = client.post(
        "/orders/checkout",
        json=checkout_payload(draft_cart_code),
        headers=auth_headers(token),
    )

    assert draft_checkout_response.status_code == 201
    assert draft_checkout_response.json()["discount_cents"] == 0
    assert draft_checkout_response.json()["payable_cents"] == 3798
    assert draft_checkout_response.json()["promotion_code"] is None

    activate_response = client.post(
        f"/admin/promotions/{promotion_code}/activate",
        headers=ADMIN_HEADERS,
    )
    assert activate_response.status_code == 200

    active_cart_code = create_cart_with_item(client)
    active_checkout_response = client.post(
        "/orders/checkout",
        json=checkout_payload(active_cart_code),
        headers=auth_headers(token),
    )

    assert active_checkout_response.status_code == 201
    assert active_checkout_response.json()["discount_cents"] == 379
    assert active_checkout_response.json()["payable_cents"] == 3419
    assert active_checkout_response.json()["promotion_code"] == promotion_code
    assert active_checkout_response.json()["payment"]["amount_cents"] == 3419

    deactivate_response = client.post(
        f"/admin/promotions/{promotion_code}/deactivate",
        headers=ADMIN_HEADERS,
    )
    assert deactivate_response.status_code == 200

    paused_cart_code = create_cart_with_item(client)
    paused_checkout_response = client.post(
        "/orders/checkout",
        json=checkout_payload(paused_cart_code),
        headers=auth_headers(token),
    )

    assert paused_checkout_response.status_code == 201
    assert paused_checkout_response.json()["discount_cents"] == 0
    assert paused_checkout_response.json()["payable_cents"] == 3798
    assert paused_checkout_response.json()["promotion_code"] is None
