from uuid import uuid4

from fastapi.testclient import TestClient

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
