from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import PublishedPrice, PublishedProduct, PublishedSku
from app.main import app


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].lower()}"


def _seed_published_catalog(
    *,
    price_cents: int = 1299,
    display_status: str = "visible",
    sell_status: str = "sellable",
    is_sellable: bool = True,
    price_is_active: bool = True,
) -> dict[str, str | int]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    publish_version = _code("pub")
    product_code = _code("pet-product")
    sku_code = _code("pet-sku")
    category_code = _code("cat")
    now = datetime.now(UTC)

    with session_factory() as session:
        session.add(
            PublishedProduct(
                publish_version=publish_version,
                pms_item_id=None,
                pms_sku=None,
                product_code=product_code,
                product_name="PMS 商品名",
                display_name="Published 猫粮",
                description="Published 商品描述",
                image_url="https://example.test/product.png",
                category_code=category_code,
                category_name="Published 类目",
                brand_code="brand_test",
                brand_name="Published 品牌",
                display_status=display_status,
                sell_status=sell_status,
                sort_order=10,
                visible_from=None,
                visible_until=None,
                published_at=now,
                source_product_id=1,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
            )
        )
        session.flush()

        session.add(
            PublishedSku(
                publish_version=publish_version,
                product_code=product_code,
                sku_code=sku_code,
                sku_name="PMS 商品名",
                display_sku_name="Published SKU",
                sales_unit_code="bag",
                sales_unit_name="袋",
                barcode="6900000000000",
                spec_text="1kg/袋",
                is_sellable=is_sellable,
                sort_order=10,
                published_at=now,
                source_sku_id=2,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
            )
        )
        session.flush()

        session.add(
            PublishedPrice(
                publish_version=publish_version,
                price_list_code="default",
                channel="storefront",
                sku_code=sku_code,
                currency="USD",
                price_cents=price_cents,
                compare_at_price_cents=None,
                effective_from=None,
                effective_until=None,
                is_active=price_is_active,
                priority=10,
                published_at=now,
                source_price_id=3,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
            )
        )
        session.commit()

    return {
        "publish_version": publish_version,
        "product_code": product_code,
        "sku_code": sku_code,
        "category_code": category_code,
        "price_cents": price_cents,
    }


def test_catalog_health() -> None:
    client = TestClient(app)

    response = client.get("/catalog/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "catalog",
        "data_source": "d2c_database_catalog",
    }


def test_catalog_categories_returns_published_categories() -> None:
    values = _seed_published_catalog()
    client = TestClient(app)

    response = client.get("/catalog/categories")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_database_catalog"
    assert payload["count"] >= 1

    category_by_code = {category["code"]: category for category in payload["categories"]}
    category = category_by_code[values["category_code"]]
    assert category["name"] == "Published 类目"
    assert category["sort_order"] == 10


def test_catalog_products_returns_published_products() -> None:
    values = _seed_published_catalog(price_cents=1888)
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200

    payload = response.json()
    products = payload["products"]

    assert payload["data_source"] == "d2c_database_catalog"
    assert payload["count"] >= 1

    product_by_id = {product["product_id"]: product for product in products}
    product = product_by_id[values["product_code"]]

    assert product["product_id"] == values["product_code"]
    assert product["sku"] == values["sku_code"]
    assert product["name"] == "Published 猫粮"
    assert product["category"] == "Published 类目"
    assert product["description"] == "Published 商品描述"
    assert product["price_cents"] == 1888
    assert product["currency"] == "USD"
    assert product["status"] == "active"
    assert product["stock_status"] == "in_stock"
    assert product["image_url"] == "https://example.test/product.png"
    assert "Published 类目" in product["tags"]
    assert "Published 品牌" in product["tags"]


def test_catalog_product_detail_returns_published_product() -> None:
    values = _seed_published_catalog(price_cents=1777)
    client = TestClient(app)

    response = client.get(f"/catalog/products/{values['product_code']}")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == values["product_code"]
    assert payload["sku"] == values["sku_code"]
    assert payload["category"] == "Published 类目"
    assert payload["description"] == "Published 商品描述"
    assert payload["price_cents"] == 1777


def test_catalog_product_detail_returns_404_for_unknown_product() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products/unknown-product")

    assert response.status_code == 404
    assert response.json() == {"detail": "catalog_product_not_found"}


def test_catalog_ignores_hidden_or_unsellable_published_products() -> None:
    hidden_values = _seed_published_catalog(display_status="hidden")
    unsellable_values = _seed_published_catalog(sell_status="not_sellable")
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200
    product_ids = {product["product_id"] for product in response.json()["products"]}

    assert hidden_values["product_code"] not in product_ids
    assert unsellable_values["product_code"] not in product_ids


def test_catalog_ignores_unsellable_skus_or_inactive_prices() -> None:
    unsellable_sku_values = _seed_published_catalog(is_sellable=False)
    inactive_price_values = _seed_published_catalog(price_is_active=False)
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200
    product_ids = {product["product_id"] for product in response.json()["products"]}

    assert unsellable_sku_values["product_code"] not in product_ids
    assert inactive_price_values["product_code"] not in product_ids


def test_catalog_repo_no_longer_reads_old_catalog_owner_tables() -> None:
    repo_text = open(
        "app/domains/catalog/repos/storefront_catalog_repo.py", encoding="utf-8"
    ).read()
    service_text = open(
        "app/domains/catalog/services/storefront_catalog_service.py",
        encoding="utf-8",
    ).read()

    forbidden_tokens = [
        "ProductCategory",
        "ProductSku",
        "PriceList",
        "SkuPrice",
        "d2c_products",
        "d2c_product_skus",
        "d2c_price_lists",
        "d2c_sku_prices",
        "d2c_product_categories",
    ]

    for token in forbidden_tokens:
        assert token not in repo_text
        assert token not in service_text
