from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app
from tests.helpers.published_catalog import (
    seed_default_published_catalog,
    seed_published_promotion,
)


def reset_promotions_for_checkout_flow() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM d2c_published_coupons"))
            connection.execute(text("DELETE FROM d2c_published_promotion_targets"))
            connection.execute(text("DELETE FROM d2c_published_promotion_rules"))
            connection.execute(text("DELETE FROM d2c_published_promotions"))
    finally:
        engine.dispose()


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16].upper()}"


def unique_email() -> str:
    return f"backoffice-promo-flow-{uuid4().hex}@example.com"


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
    seed_default_published_catalog()
    identity = cart_identity()
    response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "offer-cat-food-salmon-001",
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


def create_published_promotion(*, is_active: bool = False) -> tuple[str, str]:
    promotion_code = unique_code("FLOWPROMO")
    row = seed_published_promotion(
        promotion_code=promotion_code,
        promotion_name="后台发布后前台执行测试",
        is_active=is_active,
    )
    return promotion_code, str(row["publish_version"])


def set_published_promotion_active(
    *,
    publish_version: str,
    promotion_code: str,
    is_active: bool,
) -> None:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE d2c_published_promotion_rules
                    SET is_active = :is_active,
                        updated_at = now()
                    WHERE publish_version = :publish_version
                      AND promotion_code = :promotion_code
                    """
                ),
                {
                    "publish_version": publish_version,
                    "promotion_code": promotion_code,
                    "is_active": is_active,
                },
            )
    finally:
        engine.dispose()


def test_seeded_published_promotion_is_applied_then_deactivated() -> None:
    reset_promotions_for_checkout_flow()
    client = TestClient(app)
    promotion_code, publish_version = create_published_promotion(is_active=False)

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

    set_published_promotion_active(
        publish_version=publish_version,
        promotion_code=promotion_code,
        is_active=True,
    )

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

    set_published_promotion_active(
        publish_version=publish_version,
        promotion_code=promotion_code,
        is_active=False,
    )

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
