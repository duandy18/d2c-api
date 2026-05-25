from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import load_settings
from app.main import app
from tests.helpers.published_catalog import (
    seed_default_published_catalog,
    seed_published_offer_catalog_item,
)


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
    seed_default_published_catalog()
    client = TestClient(app)
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

    payload = response.json()
    assert payload["line_count"] == 1
    assert payload["item_count"] == 2
    assert payload["subtotal_cents"] == 3798
    assert payload["lines"] == [
        {
            "offer_code": "offer-cat-food-salmon-001",
            "name": "三文鱼成猫粮 1kg",
            "quantity": 2,
            "unit_price_cents": 1899,
            "currency": "USD",
            "line_subtotal_cents": 3798,
        }
    ]


def test_upsert_cart_item_quantity_zero_removes_line() -> None:
    seed_default_published_catalog()
    client = TestClient(app)
    identity = cart_identity()

    add_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "offer-cat-food-salmon-001",
            "quantity": 2,
        },
    )
    remove_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "offer-cat-food-salmon-001",
            "quantity": 0,
        },
    )

    assert add_response.status_code == 200
    assert remove_response.status_code == 200
    assert remove_response.json()["line_count"] == 0
    assert remove_response.json()["item_count"] == 0
    assert remove_response.json()["subtotal_cents"] == 0


def test_clear_cart_removes_all_lines() -> None:
    seed_default_published_catalog()
    client = TestClient(app)
    identity = cart_identity()

    first_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "offer-cat-food-salmon-001",
            "quantity": 2,
        },
    )
    second_response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "offer-cat-litter-tofu-001",
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


def test_upsert_cart_item_rejects_unknown_offer() -> None:
    client = TestClient(app)
    identity = cart_identity()

    response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "missing-offer",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "cart_offer_not_found"}


def test_cart_summary_fields_are_persisted() -> None:
    seed_default_published_catalog()
    client = TestClient(app)
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

    cart_payload = response.json()
    assert cart_payload["line_count"] == 1
    assert cart_payload["item_count"] == 2
    assert cart_payload["subtotal_cents"] == 3798

    engine = create_engine(load_settings().database_url)
    try:
        with engine.connect() as connection:
            cart_row = (
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
            line_row = (
                connection.execute(
                    text(
                        """
                        SELECT
                          product_id,
                          sku_id,
                          publish_version,
                          offer_code,
                          offer_title,
                          offer_type,
                          offer_subtitle,
                          group_code,
                          group_name,
                          price_code,
                          source_offer_id,
                          source_position_id,
                          product_code,
                          sku_code,
                          product_name,
                          sku_name,
                          pms_item_id,
                          pms_sku,
                          category_code,
                          category_name,
                          sales_unit_code,
                          sales_unit_name,
                          barcode,
                          price_list_code,
                          compare_at_price_cents,
                          source_product_id,
                          source_sku_id,
                          source_price_id
                        FROM d2c_cart_lines
                        WHERE cart_id = (
                          SELECT id FROM d2c_carts WHERE cart_code = :cart_code
                        )
                        """
                    ),
                    {"cart_code": cart_payload["cart_code"]},
                )
                .mappings()
                .one()
            )
    finally:
        engine.dispose()

    assert cart_row["line_count"] == 1
    assert cart_row["item_count"] == 2
    assert cart_row["subtotal_cents"] == 3798
    assert line_row["product_id"] is None
    assert line_row["sku_id"] is None
    assert line_row["publish_version"].startswith("TEST-PUB-")

    assert line_row["offer_code"] == "offer-cat-food-salmon-001"
    assert line_row["offer_title"] == "三文鱼成猫粮 1kg"
    assert line_row["offer_type"] == "single"
    assert line_row["offer_subtitle"] == "三文鱼成猫粮 1kg subtitle"
    assert line_row["group_code"] == "cat_food"
    assert line_row["group_name"] == "猫粮"
    assert line_row["price_code"] == "price-offer-cat-food-salmon-001"
    assert line_row["source_offer_id"] == 501
    assert line_row["source_position_id"] == 801

    assert line_row["product_code"] == "offer-cat-food-salmon-001"
    assert line_row["sku_code"] == "CAT-FOOD-SALMON-1KG"
    assert line_row["product_name"] == "三文鱼成猫粮 1kg"
    assert line_row["sku_name"] == "CAT-FOOD-SALMON-1KG"
    assert line_row["pms_item_id"] == 1001
    assert line_row["pms_sku"] == "PMS-CAT-FOOD-SALMON"
    assert line_row["category_code"] == "cat_food"
    assert line_row["category_name"] == "猫粮"
    assert line_row["sales_unit_code"] == "bag"
    assert line_row["sales_unit_name"] == "袋"
    assert line_row["barcode"] == "6900000000000"
    assert line_row["price_list_code"] == "price-offer-cat-food-salmon-001"
    assert line_row["compare_at_price_cents"] == 2299
    assert line_row["source_product_id"] == 501
    assert line_row["source_sku_id"] == 601
    assert line_row["source_price_id"] == 701


def test_cart_item_price_uses_published_offer_price() -> None:
    client = TestClient(app)
    identity = cart_identity()
    test_price_cents = 1777

    seed_published_offer_catalog_item(
        offer_code="offer-cat-food-salmon-price-test",
        sku_code="CAT-FOOD-SALMON-1KG",
        display_name="三文鱼成猫粮 1kg",
        price_cents=test_price_cents,
    )

    response = client.post(
        "/cart/items",
        json={
            **identity,
            "offer_code": "offer-cat-food-salmon-price-test",
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


def test_cart_repo_service_read_terminal_offer_snapshot_tables_only() -> None:
    repo_text = open("app/domains/cart/repos/cart_repo.py", encoding="utf-8").read()
    service_text = open(
        "app/domains/cart/services/storefront_cart_service.py",
        encoding="utf-8",
    ).read()

    required_tokens = [
        "PublishedOffer",
        "PublishedOfferPrice",
        "PublishedOfferComponent",
    ]
    forbidden_tokens = [
        "PublishedProduct",
        "PublishedSku",
        "PublishedPrice",
        "PriceList",
        "ProductSku",
        "SkuPrice",
        "d2c_products",
        "d2c_product_skus",
        "d2c_price_lists",
        "d2c_sku_prices",
    ]

    for token in required_tokens:
        assert token in repo_text

    for token in forbidden_tokens:
        assert token not in repo_text
        assert token not in service_text
