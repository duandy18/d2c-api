from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


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
            connection.execute(
                text(
                    """
                    UPDATE d2c_coupons
                    SET status = 'draft',
                        is_active = FALSE
                    """
                )
            )
            connection.execute(
                text(
                    """
                    UPDATE d2c_promotions
                    SET status = 'draft',
                        is_active = FALSE
                    """
                )
            )
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
    response = client.post(
        "/cart/items",
        json={
            "anonymous_id": unique_code("anon"),
            "session_code": unique_code("sess"),
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
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


def create_active_backoffice_coupon(client: TestClient) -> tuple[str, str]:
    promotion_code = unique_code("CHECKOUTPROMO")
    coupon_code = unique_code("CHECKOUTCOUPON")

    promotion_response = client.post(
        "/backoffice/promotions",
        json={
            "promotion_code": promotion_code,
            "name": "Checkout Coupon Promotion",
            "promotion_type": "store_campaign",
            "discount_type": "percentage",
            "discount_value": 10,
            "scope_type": "all_store",
            "currency": "USD",
            "priority": 10,
            "stackable": False,
        },
        headers=BACKOFFICE_HEADERS,
    )
    assert promotion_response.status_code == 201

    activate_promotion_response = client.post(
        f"/backoffice/promotions/{promotion_code}/activate",
        headers=BACKOFFICE_HEADERS,
    )
    assert activate_promotion_response.status_code == 200

    coupon_response = client.post(
        f"/backoffice/promotions/{promotion_code}/coupons",
        json={
            "coupon_code": coupon_code,
            "name": "Checkout Coupon",
            "coupon_type": "public_code",
            "total_limit": 100,
            "per_customer_limit": 1,
        },
        headers=BACKOFFICE_HEADERS,
    )
    assert coupon_response.status_code == 201

    activate_coupon_response = client.post(
        f"/backoffice/promotions/coupons/{coupon_code}/activate",
        headers=BACKOFFICE_HEADERS,
    )
    assert activate_coupon_response.status_code == 200

    return promotion_code, coupon_code


def test_checkout_applies_active_public_coupon_code() -> None:
    reset_promotions_and_coupons()
    client = TestClient(app)
    token = register_customer(client)
    promotion_code, coupon_code = create_active_backoffice_coupon(client)
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
                          coupon_code,
                          coupon_id,
                          promotion_code,
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
    finally:
        engine.dispose()

    assert order_row["coupon_code"] == coupon_code
    assert order_row["coupon_id"] is not None
    assert order_row["promotion_code"] == promotion_code
    assert order_row["discount_cents"] == 379
    assert order_row["payable_cents"] == 3419


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
    _, coupon_code = create_active_backoffice_coupon(client)

    deactivate_coupon_response = client.post(
        f"/backoffice/promotions/coupons/{coupon_code}/deactivate",
        headers=BACKOFFICE_HEADERS,
    )
    assert deactivate_coupon_response.status_code == 200

    cart_code = create_cart_with_item(client)
    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code, coupon_code),
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "checkout_coupon_not_available"}
