from fastapi.testclient import TestClient

from app.main import app

BACKOFFICE_HEADERS = {"X-Backoffice-Client": "d2c-backoffice"}


def test_backoffice_catalog_requires_backoffice_client() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/units")

    assert response.status_code == 401
    assert response.json() == {"detail": "backoffice_client_required"}


def test_backoffice_catalog_health() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/health", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "backoffice_catalog",
        "surface": "merchant_read",
    }


def test_backoffice_catalog_units_returns_seeded_units() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/units", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] >= 8
    unit_codes = {unit["unit_code"] for unit in payload["units"]}
    assert {"piece", "pack", "bag", "kg", "l"}.issubset(unit_codes)


def test_backoffice_catalog_price_lists_returns_default_storefront_price_list() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/price-lists", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] >= 1

    default_price_list = payload["price_lists"][0]
    assert default_price_list["price_list_code"] == "default_usd_storefront"
    assert default_price_list["currency"] == "USD"
    assert default_price_list["channel"] == "storefront"
    assert default_price_list["customer_segment"] == "default"
    assert default_price_list["is_default"] is True


def test_backoffice_catalog_products_returns_management_view() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/products", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 6

    first = payload["products"][0]
    assert first["product_code"] == "pet-cat-food-salmon-001"
    assert first["category_code"] == "cat_food"
    assert first["category_name"] == "猫粮"
    assert first["status"] == "active"


def test_backoffice_catalog_skus_returns_units_and_storefront_prices() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/skus", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 6

    sku_by_code = {sku["sku_code"]: sku for sku in payload["skus"]}
    salmon_sku = sku_by_code["CAT-FOOD-SALMON-1KG"]

    assert salmon_sku["product_code"] == "pet-cat-food-salmon-001"
    assert salmon_sku["sales_unit_code"] == "bag"
    assert salmon_sku["package_unit_text"] == "1kg"
    assert salmon_sku["legacy_price_cents"] == 1899
    assert salmon_sku["storefront_price_cents"] == 1899


def test_backoffice_catalog_sku_prices_returns_default_sku_prices() -> None:
    client = TestClient(app)

    response = client.get("/backoffice/catalog/sku-prices", headers=BACKOFFICE_HEADERS)

    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 6

    price_by_sku = {price["sku_code"]: price for price in payload["sku_prices"]}
    salmon_price = price_by_sku["CAT-FOOD-SALMON-1KG"]

    assert salmon_price["price_list_code"] == "default_usd_storefront"
    assert salmon_price["channel"] == "storefront"
    assert salmon_price["customer_segment"] == "default"
    assert salmon_price["price_cents"] == 1899
    assert salmon_price["currency"] == "USD"
