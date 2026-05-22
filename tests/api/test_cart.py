from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app


def unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def cart_identity() -> dict[str, str]:
    return {
        "anonymous_id": unique_code("anon"),
        "session_code": unique_code("sess"),
    }


def test_cart_health() -> None:
    client = TestClient(app)

    response = client.get("/cart/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "cart",
        "storage": "d2c_carts",
    }


def test_get_empty_cart_creates_cart() -> None:
    client = TestClient(app)
    identity = cart_identity()

    response = client.get("/cart", params=identity)

    assert response.status_code == 200

    payload = response.json()
    assert payload["cart_code"].startswith("CART-")
    assert payload["anonymous_id"] == identity["anonymous_id"]
    assert payload["session_code"] == identity["session_code"]
    assert payload["line_count"] == 0
    assert payload["item_count"] == 0
    assert payload["subtotal_cents"] == 0
    assert payload["lines"] == []


def test_upsert_cart_item_sets_quantity_and_subtotal() -> None:
    client = TestClient(app)
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

    payload = response.json()
    assert payload["line_count"] == 1
    assert payload["item_count"] == 2
    assert payload["subtotal_cents"] == 3798
    assert payload["lines"] == [
        {
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
            "name": "三文鱼成猫粮 1kg",
            "quantity": 2,
            "unit_price_cents": 1899,
            "currency": "USD",
            "line_subtotal_cents": 3798,
        }
    ]


def test_upsert_cart_item_quantity_zero_removes_line() -> None:
    client = TestClient(app)
    identity = cart_identity()

    add_response = client.post(
        "/cart/items",
        json={
            **identity,
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
            "quantity": 2,
        },
    )
    remove_response = client.post(
        "/cart/items",
        json={
            **identity,
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
            "quantity": 0,
        },
    )

    assert add_response.status_code == 200
    assert remove_response.status_code == 200
    assert remove_response.json()["line_count"] == 0
    assert remove_response.json()["item_count"] == 0
    assert remove_response.json()["subtotal_cents"] == 0


def test_clear_cart_removes_all_lines() -> None:
    client = TestClient(app)
    identity = cart_identity()

    first_response = client.post(
        "/cart/items",
        json={
            **identity,
            "product_id": "pet-cat-food-salmon-001",
            "sku": "CAT-FOOD-SALMON-1KG",
            "quantity": 2,
        },
    )
    second_response = client.post(
        "/cart/items",
        json={
            **identity,
            "product_id": "pet-cat-litter-tofu-001",
            "sku": "CAT-LITTER-TOFU-6L",
            "quantity": 1,
        },
    )
    clear_response = client.post("/cart/clear", json=identity)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert clear_response.status_code == 200
    assert clear_response.json()["line_count"] == 0
    assert clear_response.json()["item_count"] == 0
    assert clear_response.json()["subtotal_cents"] == 0


def test_upsert_cart_item_rejects_unknown_product() -> None:
    client = TestClient(app)
    identity = cart_identity()

    response = client.post(
        "/cart/items",
        json={
            **identity,
            "product_id": "missing-product",
            "sku": "MISSING-SKU",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "cart_product_not_found"}


def test_cart_summary_fields_are_persisted() -> None:
    client = TestClient(app)
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

    cart_payload = response.json()
    assert cart_payload["line_count"] == 1
    assert cart_payload["item_count"] == 2
    assert cart_payload["subtotal_cents"] == 3798

    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                        SELECT line_count, item_count, subtotal_cents
                        FROM d2c_carts
                        WHERE cart_code = :cart_code
                        """
                    ),
                    {"cart_code": cart_payload["cart_code"]},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    assert row["line_count"] == 1
    assert row["item_count"] == 2
    assert row["subtotal_cents"] == 3798


def test_cart_item_price_uses_default_sku_price() -> None:
    client = TestClient(app)
    identity = cart_identity()
    sku_code = "CAT-FOOD-SALMON-1KG"
    test_price_cents = 1777

    engine = create_engine(load_settings().database_url)
    with engine.begin() as connection:
        original_price = connection.execute(
            text(
                """
                SELECT sp.price_cents
                FROM d2c_sku_prices sp
                JOIN d2c_product_skus s ON s.id = sp.sku_id
                JOIN d2c_price_lists pl ON pl.id = sp.price_list_id
                WHERE s.sku_code = :sku_code
                  AND pl.price_list_code = 'default_usd_storefront'
                """
            ),
            {"sku_code": sku_code},
        ).scalar_one()

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE d2c_sku_prices sp
                    SET price_cents = :price_cents
                    FROM d2c_product_skus s, d2c_price_lists pl
                    WHERE sp.sku_id = s.id
                      AND sp.price_list_id = pl.id
                      AND s.sku_code = :sku_code
                      AND pl.price_list_code = 'default_usd_storefront'
                    """
                ),
                {
                    "sku_code": sku_code,
                    "price_cents": test_price_cents,
                },
            )

        response = client.post(
            "/cart/items",
            json={
                **identity,
                "product_id": "pet-cat-food-salmon-001",
                "sku": sku_code,
                "quantity": 2,
            },
        )

        assert response.status_code == 200

        payload = response.json()
        assert payload["line_count"] == 1
        assert payload["item_count"] == 2
        assert payload["subtotal_cents"] == test_price_cents * 2
        assert payload["lines"][0]["unit_price_cents"] == test_price_cents
        assert payload["lines"][0]["line_subtotal_cents"] == test_price_cents * 2
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE d2c_sku_prices sp
                    SET price_cents = :price_cents
                    FROM d2c_product_skus s, d2c_price_lists pl
                    WHERE sp.sku_id = s.id
                      AND sp.price_list_id = pl.id
                      AND s.sku_code = :sku_code
                      AND pl.price_list_code = 'default_usd_storefront'
                    """
                ),
                {
                    "sku_code": sku_code,
                    "price_cents": original_price,
                },
            )
        engine.dispose()
