from fastapi.testclient import TestClient

from app.main import app


def test_catalog_health() -> None:
    client = TestClient(app)

    response = client.get("/catalog/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "catalog",
        "data_source": "placeholder_static_catalog",
        "future_source": "pms_projection",
    }


def test_catalog_products_returns_pet_multi_sku_placeholder_products() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200

    payload = response.json()
    products = payload["products"]

    assert payload["data_source"] == "placeholder_static_catalog"
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
    assert all("未来来自 PMS projection" in product["description"] for product in products)


def test_catalog_product_detail_returns_placeholder_product() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products/pet-cat-food-salmon-001")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == "pet-cat-food-salmon-001"
    assert payload["sku"] == "CAT-FOOD-SALMON-1KG"
    assert payload["category"] == "猫粮"
    assert "未来来自 PMS projection" in payload["description"]


def test_catalog_product_detail_returns_404_for_unknown_product() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products/unknown-product")

    assert response.status_code == 404
    assert response.json() == {"detail": "catalog_product_not_found"}
