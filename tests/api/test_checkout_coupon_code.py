from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app
from tests.helpers.published_catalog import (
    seed_default_published_catalog,
    seed_published_coupon,
    seed_published_promotion,
)


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16].upper()}"


def unique_email() -> str:
    return f"checkout-coupon-{uuid4().hex}@example.com"


def unique_phone() -> str:
    return f"166{uuid4().hex[:8]}"


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def reset_promotions_and_coupons() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM d2c_published_coupons"))
            connection.execute(text("DELETE FROM d2c_published_promotion_targets"))
            connection.execute(text("DELETE FROM d2c_published_promotion_rules"))
    finally:
        engine.dispose()


def register_customer(client: TestClient) -> str:
    response = client.post(
        "/customers/register",
        json={
            "email": unique_email(),
            "password": "StrongPass123",
            "display_name": "Checkout Coupon Customer",
            "phone": unique_phone(),
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def create_cart_with_item(client: TestClient) -> str:
    seed_default_published_catalog()
    response = client.post(
        "/cart/items",
        json={
            "anonymous_id": unique_code("anon"),
            "session_code": unique_code("sess"),
            "offer_code": "offer-cat-food-salmon-001",
            "quantity": 2,
        },
    )
    assert response.status_code == 200
    return response.json()["cart_code"]


def checkout_payload(cart_code: str, coupon_code: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
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
    if coupon_code is not None:
        payload["coupon_code"] = coupon_code
    return payload


def create_active_published_coupon(
    *,
    total_limit: int | None = 100,
    per_customer_limit: int | None = 1,
) -> tuple[str, str, str]:
    promotion_code = unique_code("CHECKOUTPROMO")
    coupon_code = unique_code("CHECKOUTCOUPON")
    promotion = seed_published_promotion(
        promotion_code=promotion_code,
        promotion_name="Checkout Coupon Promotion",
        is_active=True,
    )
    publish_version = str(promotion["publish_version"])
    seed_published_coupon(
        publish_version=publish_version,
        coupon_code=coupon_code,
        coupon_name="Checkout Coupon",
        promotion_code=promotion_code,
        total_limit=total_limit,
        per_customer_limit=per_customer_limit,
        is_active=True,
    )
    return publish_version, promotion_code, coupon_code


def set_published_coupon_active(
    *,
    publish_version: str,
    coupon_code: str,
    is_active: bool,
) -> None:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE d2c_published_coupons
                    SET is_active = :is_active,
                        updated_at = now()
                    WHERE publish_version = :publish_version
                      AND coupon_code = :coupon_code
                    """
                ),
                {
                    "publish_version": publish_version,
                    "coupon_code": coupon_code,
                    "is_active": is_active,
                },
            )
    finally:
        engine.dispose()


def test_checkout_applies_active_public_coupon_code() -> None:
    reset_promotions_and_coupons()
    client = TestClient(app)
    token = register_customer(client)
    publish_version, promotion_code, coupon_code = create_active_published_coupon()
    cart_code = create_cart_with_item(client)

    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code, coupon_code),
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["subtotal_cents"] == 3798
    assert payload["discount_cents"] == 379
    assert payload["payable_cents"] == 3419
    assert payload["promotion_code"] == promotion_code
    assert payload["coupon_code"] == coupon_code
    assert payload["payment"]["amount_cents"] == 3419

    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            order_row = (
                connection.execute(
                    text(
                        """
                        SELECT
                          id,
                          coupon_code,
                          coupon_name,
                          coupon_type,
                          coupon_publish_version,
                          promotion_code,
                          promotion_name,
                          promotion_type,
                          promotion_discount_type,
                          promotion_discount_value,
                          promotion_publish_version,
                          discount_cents,
                          payable_cents
                        FROM d2c_orders
                        WHERE order_no = :order_no
                        """
                    ),
                    {"order_no": payload["order_no"]},
                )
                .mappings()
                .one()
            )
            customer_coupon_row = (
                connection.execute(
                    text(
                        """
                        SELECT
                          customer_coupon_code,
                          publish_version,
                          coupon_code,
                          coupon_name,
                          coupon_type,
                          promotion_code,
                          promotion_name,
                          promotion_type,
                          promotion_discount_type,
                          promotion_discount_value,
                          customer_id,
                          status,
                          claimed_at,
                          used_at,
                          order_id,
                          order_no
                        FROM d2c_customer_coupons
                        WHERE order_id = :order_id
                        """
                    ),
                    {"order_id": order_row["id"]},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    assert order_row["coupon_code"] == coupon_code
    assert order_row["coupon_name"] == "Checkout Coupon"
    assert order_row["coupon_type"] == "public_code"
    assert order_row["coupon_publish_version"] == publish_version
    assert order_row["promotion_code"] == promotion_code
    assert order_row["promotion_name"] == "Checkout Coupon Promotion"
    assert order_row["promotion_type"] == "store_campaign"
    assert order_row["promotion_discount_type"] == "percentage"
    assert order_row["promotion_discount_value"] == 10
    assert order_row["promotion_publish_version"] == publish_version
    assert order_row["discount_cents"] == 379
    assert order_row["payable_cents"] == 3419

    assert customer_coupon_row["customer_coupon_code"].startswith("CCPN-")
    assert customer_coupon_row["publish_version"] == publish_version
    assert customer_coupon_row["coupon_code"] == coupon_code
    assert customer_coupon_row["coupon_name"] == "Checkout Coupon"
    assert customer_coupon_row["coupon_type"] == "public_code"
    assert customer_coupon_row["promotion_code"] == promotion_code
    assert customer_coupon_row["promotion_name"] == "Checkout Coupon Promotion"
    assert customer_coupon_row["promotion_type"] == "store_campaign"
    assert customer_coupon_row["promotion_discount_type"] == "percentage"
    assert customer_coupon_row["promotion_discount_value"] == 10
    assert customer_coupon_row["status"] == "used"
    assert customer_coupon_row["claimed_at"] is not None
    assert customer_coupon_row["used_at"] is not None
    assert customer_coupon_row["order_id"] == order_row["id"]
    assert customer_coupon_row["order_no"] == payload["order_no"]


def test_checkout_rejects_unknown_coupon_code() -> None:
    reset_promotions_and_coupons()
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_cart_with_item(client)

    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code, "UNKNOWN-COUPON"),
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "checkout_coupon_not_available"}


def test_checkout_does_not_use_inactive_coupon_code() -> None:
    reset_promotions_and_coupons()
    client = TestClient(app)
    token = register_customer(client)
    publish_version, _, coupon_code = create_active_published_coupon()

    set_published_coupon_active(
        publish_version=publish_version,
        coupon_code=coupon_code,
        is_active=False,
    )

    cart_code = create_cart_with_item(client)
    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code, coupon_code),
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "checkout_coupon_not_available"}


def test_checkout_enforces_coupon_per_customer_limit() -> None:
    reset_promotions_and_coupons()
    client = TestClient(app)
    token = register_customer(client)
    _, _, coupon_code = create_active_published_coupon(
        total_limit=100,
        per_customer_limit=1,
    )

    first_cart_code = create_cart_with_item(client)
    first_response = client.post(
        "/orders/checkout",
        json=checkout_payload(first_cart_code, coupon_code),
        headers=auth_headers(token),
    )
    assert first_response.status_code == 201

    second_cart_code = create_cart_with_item(client)
    second_response = client.post(
        "/orders/checkout",
        json=checkout_payload(second_cart_code, coupon_code),
        headers=auth_headers(token),
    )

    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "checkout_coupon_usage_limit_exceeded"}


def test_checkout_enforces_coupon_total_limit() -> None:
    reset_promotions_and_coupons()
    client = TestClient(app)
    first_token = register_customer(client)
    second_token = register_customer(client)
    _, _, coupon_code = create_active_published_coupon(
        total_limit=1,
        per_customer_limit=10,
    )

    first_cart_code = create_cart_with_item(client)
    first_response = client.post(
        "/orders/checkout",
        json=checkout_payload(first_cart_code, coupon_code),
        headers=auth_headers(first_token),
    )
    assert first_response.status_code == 201

    second_cart_code = create_cart_with_item(client)
    second_response = client.post(
        "/orders/checkout",
        json=checkout_payload(second_cart_code, coupon_code),
        headers=auth_headers(second_token),
    )

    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "checkout_coupon_usage_limit_exceeded"}
