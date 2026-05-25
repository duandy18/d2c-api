from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPosition,
    PublishedOfferPrice,
)
from app.main import app


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].lower()}"


def _seed_published_offer_catalog(
    *,
    price_cents: int = 1299,
    group_display_status: str = "visible",
    group_is_active: bool = True,
    offer_display_status: str = "visible",
    offer_sell_status: str = "sellable",
    price_is_active: bool = True,
    position_is_active: bool = True,
) -> dict[str, str | int]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    publish_version = _code("pub")
    group_code = _code("group")
    offer_code = _code("offer")
    price_code = _code("price")
    position_code = _code("pos")
    now = datetime.now(UTC)

    with session_factory() as session:
        session.add(
            PublishedGroup(
                publish_version=publish_version,
                group_code=group_code,
                group_name="Published Group 猫粮",
                group_kind="category",
                description="pytest group",
                image_url=None,
                sort_order=10,
                display_status=group_display_status,
                is_active=group_is_active,
                source_group_id=1,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOffer(
                publish_version=publish_version,
                offer_code=offer_code,
                offer_type="single",
                title="Published Offer 猫粮",
                subtitle="Offer subtitle",
                description="Published Offer 描述",
                image_url="https://example.test/offer.png",
                display_status=offer_display_status,
                sell_status=offer_sell_status,
                source_offer_id=2,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOfferPrice(
                publish_version=publish_version,
                offer_code=offer_code,
                price_code=price_code,
                channel="storefront",
                currency="USD",
                price_cents=price_cents,
                compare_at_price_cents=price_cents + 300,
                effective_from=None,
                effective_until=None,
                is_active=price_is_active,
                priority=10,
                source_price_id=3,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOfferPosition(
                publish_version=publish_version,
                position_code=position_code,
                group_code=group_code,
                offer_code=offer_code,
                sort_order=1,
                position_source="manual",
                is_featured=True,
                visible_from=None,
                visible_until=None,
                is_active=position_is_active,
                source_position_id=4,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.commit()

    return {
        "publish_version": publish_version,
        "group_code": group_code,
        "offer_code": offer_code,
        "price_code": price_code,
        "position_code": position_code,
        "price_cents": price_cents,
    }


def test_catalog_health() -> None:
    client = TestClient(app)

    response = client.get("/catalog/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "module": "catalog",
        "data_source": "d2c_published_offer_snapshot",
    }


def test_catalog_categories_returns_published_groups() -> None:
    values = _seed_published_offer_catalog()
    client = TestClient(app)

    response = client.get("/catalog/categories")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_published_offer_snapshot"
    assert payload["count"] >= 1

    category_by_code = {category["code"]: category for category in payload["categories"]}
    category = category_by_code[values["group_code"]]
    assert category["name"] == "Published Group 猫粮"
    assert category["sort_order"] == 10


def test_catalog_products_returns_published_offers() -> None:
    values = _seed_published_offer_catalog(price_cents=1888)
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200

    payload = response.json()
    products = payload["products"]

    assert payload["data_source"] == "d2c_published_offer_snapshot"
    assert payload["count"] >= 1

    product_by_id = {product["product_id"]: product for product in products}
    product = product_by_id[values["offer_code"]]

    assert product["product_id"] == values["offer_code"]
    assert product["sku"] == values["offer_code"]
    assert product["name"] == "Published Offer 猫粮"
    assert product["category"] == "Published Group 猫粮"
    assert product["description"] == "Published Offer 描述"
    assert product["price_cents"] == 1888
    assert product["currency"] == "USD"
    assert product["status"] == "active"
    assert product["stock_status"] == "in_stock"
    assert product["image_url"] == "https://example.test/offer.png"
    assert "Published Group 猫粮" in product["tags"]
    assert "single" in product["tags"]


def test_catalog_product_detail_returns_published_offer() -> None:
    values = _seed_published_offer_catalog(price_cents=1777)
    client = TestClient(app)

    response = client.get(f"/catalog/products/{values['offer_code']}")

    assert response.status_code == 200

    payload = response.json()
    assert payload["product_id"] == values["offer_code"]
    assert payload["sku"] == values["offer_code"]
    assert payload["category"] == "Published Group 猫粮"
    assert payload["description"] == "Published Offer 描述"
    assert payload["price_cents"] == 1777


def test_catalog_product_detail_returns_404_for_unknown_product() -> None:
    client = TestClient(app)

    response = client.get("/catalog/products/unknown-product")

    assert response.status_code == 404
    assert response.json() == {"detail": "catalog_product_not_found"}


def test_catalog_ignores_hidden_or_unsellable_published_offers() -> None:
    hidden_values = _seed_published_offer_catalog(offer_display_status="hidden")
    unsellable_values = _seed_published_offer_catalog(offer_sell_status="not_sellable")
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200
    product_ids = {product["product_id"] for product in response.json()["products"]}

    assert hidden_values["offer_code"] not in product_ids
    assert unsellable_values["offer_code"] not in product_ids


def test_catalog_ignores_inactive_positions_or_prices() -> None:
    inactive_position_values = _seed_published_offer_catalog(position_is_active=False)
    inactive_price_values = _seed_published_offer_catalog(price_is_active=False)
    client = TestClient(app)

    response = client.get("/catalog/products")

    assert response.status_code == 200
    product_ids = {product["product_id"] for product in response.json()["products"]}

    assert inactive_position_values["offer_code"] not in product_ids
    assert inactive_price_values["offer_code"] not in product_ids


def test_catalog_repo_reads_terminal_offer_snapshot_tables_only() -> None:
    repo_text = open(
        "app/domains/catalog/repos/storefront_catalog_repo.py", encoding="utf-8"
    ).read()
    service_text = open(
        "app/domains/catalog/services/storefront_catalog_service.py",
        encoding="utf-8",
    ).read()

    required_tokens = [
        "PublishedGroup",
        "PublishedOffer",
        "PublishedOfferPrice",
        "PublishedOfferPosition",
    ]
    forbidden_tokens = [
        "PublishedProduct",
        "PublishedSku",
        "PublishedPrice",
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

    for token in required_tokens:
        assert token in repo_text

    for token in forbidden_tokens:
        assert token not in repo_text
        assert token not in service_text
