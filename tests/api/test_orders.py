from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app
from tests.helpers.published_catalog import (
    seed_default_published_catalog,
    seed_published_promotion,
)


@pytest.fixture(autouse=True)
def reset_active_promotions() -> None:
    engine = create_engine(load_settings().database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM d2c_published_coupons"))
            connection.execute(text("DELETE FROM d2c_published_promotions"))
        yield
        with engine.begin() as connection:
            connection.execute(text("DELETE FROM d2c_published_coupons"))
            connection.execute(text("DELETE FROM d2c_published_promotions"))
    finally:
        engine.dispose()


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def unique_email() -> str:
    return f"order-customer-{uuid4().hex}@example.com"


def unique_phone() -> str:
    return f"188{uuid4().hex[:8]}"


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def register_customer(client: TestClient) -> str:
    response = client.post(
        "/customers/register",
        json={
            "email": unique_email(),
            "password": "StrongPass123",
            "display_name": "Order Customer",
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
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
            "quantity": 2,
        },
    )
    assert response.status_code == 200
    return response.json()["cart_code"]


def create_empty_cart(client: TestClient) -> str:
    identity = cart_identity()
    response = client.get("/cart", params=identity)
    assert response.status_code == 200
    return response.json()["cart_code"]


def create_active_all_store_percentage_promotion(
    *,
    discount_value: int,
    max_discount_cents: int | None = None,
    min_order_amount_cents: int | None = None,
) -> tuple[str, str]:
    promotion_code = f"PROMO-{uuid4().hex[:16].upper()}"
    row = seed_published_promotion(
        promotion_code=promotion_code,
        promotion_name="测试全店折扣",
        discount_value=discount_value,
        min_order_amount_cents=min_order_amount_cents,
        max_discount_cents=max_discount_cents,
        is_active=True,
    )
    return promotion_code, str(row["publish_version"])


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


def test_orders_health() -> None:
    client = TestClient(app)

    response = client.get("/orders/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "orders",
        "checkout_mode": "cart_conversion",
        "payment_mode": "mock_ready",
    }


def test_checkout_requires_customer_auth() -> None:
    client = TestClient(app)
    cart_code = create_cart_with_item(client)

    response = client.post("/orders/checkout", json=checkout_payload(cart_code))

    assert response.status_code == 401
    assert response.json() == {"detail": "customer_auth_required"}


def test_checkout_rejects_empty_cart() -> None:
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_empty_cart(client)

    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "checkout_cart_empty"}


def test_checkout_converts_cart_to_pending_payment_order() -> None:
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_cart_with_item(client)

    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["order_no"].startswith("ORD-")
    assert payload["cart_code"] == cart_code
    assert payload["status"] == "pending_payment"
    assert payload["currency"] == "USD"
    assert payload["item_count"] == 2
    assert payload["subtotal_cents"] == 3798
    assert payload["discount_cents"] == 0
    assert payload["payable_cents"] == 3798
    assert payload["promotion_code"] is None
    assert payload["recipient_name"] == "Andy"
    assert payload["payment"]["payment_no"].startswith("PAY-")
    assert payload["payment"]["provider"] == "mock"
    assert payload["payment"]["payment_method"] == "mock"
    assert payload["payment"]["status"] == "pending"
    assert payload["payment"]["amount_cents"] == 3798
    assert payload["lines"] == [
        {
            "product_code": "pet-cat-food-salmon-001",
            "sku_code": "CAT-FOOD-SALMON-1KG",
            "product_name": "三文鱼成猫粮 1kg",
            "sku_name": "三文鱼成猫粮 1kg",
            "quantity": 2,
            "unit_price_cents": 1899,
            "line_subtotal_cents": 3798,
        }
    ]

    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT status, customer_id
                        FROM d2c_carts
                        WHERE cart_code = :cart_code
                        """
                    ),
                    {"cart_code": cart_code},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    assert row["status"] == "converted"
    assert row["customer_id"] is not None


def test_checkout_applies_active_all_store_percentage_promotion() -> None:
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_cart_with_item(client)
    promotion_code, publish_version = create_active_all_store_percentage_promotion(
        discount_value=10,
    )

    response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    payload = response.json()
    assert payload["subtotal_cents"] == 3798
    assert payload["discount_cents"] == 379
    assert payload["payable_cents"] == 3419
    assert payload["promotion_code"] == promotion_code
    assert payload["payment"]["amount_cents"] == 3419
    assert payload["payment"]["status"] == "pending"
    assert payload["lines"][0]["line_subtotal_cents"] == 3798

    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            order_row = (
                connection.execute(
                    text(
                        """
                        SELECT
                          discount_cents,
                          payable_cents,
                          promotion_code,
                          promotion_name,
                          promotion_type,
                          promotion_discount_type,
                          promotion_discount_value,
                          promotion_publish_version
                        FROM d2c_orders
                        WHERE order_no = :order_no
                        """
                    ),
                    {"order_no": payload["order_no"]},
                )
                .mappings()
                .one()
            )
            payment_amount = connection.execute(
                text(
                    """
                    SELECT amount_cents
                    FROM d2c_payments
                    WHERE order_no = :order_no
                    """
                ),
                {"order_no": payload["order_no"]},
            ).scalar_one()
    finally:
        engine.dispose()

    assert order_row["discount_cents"] == 379
    assert order_row["payable_cents"] == 3419
    assert order_row["promotion_code"] == promotion_code
    assert order_row["promotion_name"] == "测试全店折扣"
    assert order_row["promotion_type"] == "store_campaign"
    assert order_row["promotion_discount_type"] == "percentage"
    assert order_row["promotion_discount_value"] == 10
    assert order_row["promotion_publish_version"] == publish_version
    assert payment_amount == 3419


def test_checkout_rejects_duplicate_cart_conversion() -> None:
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_cart_with_item(client)

    first_response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )
    second_response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "checkout_cart_already_converted"}


def test_get_order_returns_customer_order() -> None:
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_cart_with_item(client)

    checkout_response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )
    order_no = checkout_response.json()["order_no"]

    response = client.get(f"/orders/{order_no}", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["order_no"] == order_no
    assert response.json()["discount_cents"] == 0
    assert response.json()["payable_cents"] == 3798
    assert response.json()["payment"]["status"] == "pending"


def test_mock_payment_marks_order_paid() -> None:
    client = TestClient(app)
    token = register_customer(client)
    cart_code = create_cart_with_item(client)

    checkout_response = client.post(
        "/orders/checkout",
        json=checkout_payload(cart_code),
        headers=auth_headers(token),
    )
    order_no = checkout_response.json()["order_no"]

    pay_response = client.post(
        f"/orders/{order_no}/pay/mock",
        headers=auth_headers(token),
    )

    assert pay_response.status_code == 200

    payload = pay_response.json()
    assert payload["order_no"] == order_no
    assert payload["status"] == "paid"
    assert payload["paid_at"] is not None
    assert payload["payable_cents"] == 3798
    assert payload["payment"]["amount_cents"] == 3798
    assert payload["payment"]["status"] == "succeeded"
    assert payload["payment"]["paid_at"] is not None
    assert payload["payment"]["provider_payment_id"].startswith("MOCK-")
    assert payload["payment"]["provider_trade_no"].startswith("MOCK-TRADE-")
