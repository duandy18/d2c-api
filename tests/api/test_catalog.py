from fastapi.testclient import TestClient

from app.main import app


def test_catalog_health() -> None:
    client = TestClient(app)

    response = client.get("/catalog/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "catalog",
        "data_source": "d2c_database_catalog",
    }


def test_catalog_categories_returns_owner_categories() -> None:
    client = TestClient(app)

    response = client.get("/catalog/categories")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_database_catalog"
    assert payload["count"] == 6
    assert [category["name"] for category in payload["categories"]] == [
        "猫粮",
        "猫砂",
        "零食",
        "玩具",
        "护理用品",
        "出行与日用品",
    ]


def test_catalog_products_returns_pet_multi_sku_products_from_database() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200

    payload = response.json()
    products = payload["products"]

    assert payload["data_source"] == "d2c_database_catalog"
    assert payload["count"] == 6
    assert len(products) == 6

    categories = {product["category"] for product in products}
    assert categories == {
        "猫粮",
        "猫砂",
        "零食",
        "玩具",
        "护理用品",
        "出行与日用品",
    }

    assert all(product["product_id"].startswith("pet-") for product in products)
    assert all(product["sku"] for product in products)
    assert all(product["price_cents"] >= 0 for product in products)


def test_catalog_product_detail_returns_database_product() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products/pet-cat-food-salmon-001")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == "pet-cat-food-salmon-001"
    assert payload["sku"] == "CAT-FOOD-SALMON-1KG"
    assert payload["category"] == "猫粮"
    assert payload["description"] == "面向成猫的三文鱼风味日常主粮，D2C 自有商城商品。"


def test_catalog_product_detail_returns_404_for_unknown_product() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products/unknown-product")

    assert response.status_code == 404
    assert response.json() == {"detail": "catalog_product_not_found"}


def test_catalog_product_price_uses_default_sku_price() -> None:
    from sqlalchemy import create_engine, text

    from app.core.config import load_settings

    client = TestClient(app)
    engine = create_engine(load_settings().database_url)
    sku_code = "CAT-FOOD-SALMON-1KG"
    test_price_cents = 1777

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

        response = client.get("/catalog/products/pet-cat-food-salmon-001")

        assert response.status_code == 200
        assert response.json()["price_cents"] == test_price_cents
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
