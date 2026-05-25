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


def _seed_home_offer(
    *,
    publish_version: str | None = None,
    group_code: str | None = None,
    group_name: str = "猫砂",
    group_kind: str = "category",
    group_sort_order: int = 10,
    group_display_status: str = "visible",
    group_is_active: bool = True,
    offer_code: str | None = None,
    offer_type: str = "single",
    title: str = "豆腐猫砂 6L",
    offer_display_status: str = "visible",
    offer_sell_status: str = "sellable",
    position_code: str | None = None,
    position_sort_order: int = 10,
    position_is_active: bool = True,
    price_code: str | None = None,
    price_cents: int = 1099,
    compare_at_price_cents: int | None = 1399,
    price_is_active: bool = True,
) -> dict[str, str | int | None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    resolved_publish_version = publish_version or _code("pub")
    resolved_group_code = group_code or _code("group")
    resolved_offer_code = offer_code or _code("offer")
    resolved_position_code = position_code or _code("pos")
    resolved_price_code = price_code or _code("price")
    now = datetime.now(UTC)

    with session_factory() as session:
        session.add(
            PublishedGroup(
                publish_version=resolved_publish_version,
                group_code=resolved_group_code,
                group_name=group_name,
                group_kind=group_kind,
                description=f"{group_name} description",
                image_url=None,
                sort_order=group_sort_order,
                display_status=group_display_status,
                is_active=group_is_active,
                source_group_id=1,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOffer(
                publish_version=resolved_publish_version,
                offer_code=resolved_offer_code,
                offer_type=offer_type,
                title=title,
                subtitle=f"{title} subtitle",
                description=f"{title} description",
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
                publish_version=resolved_publish_version,
                offer_code=resolved_offer_code,
                price_code=resolved_price_code,
                channel="storefront",
                currency="USD",
                price_cents=price_cents,
                compare_at_price_cents=compare_at_price_cents,
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
                publish_version=resolved_publish_version,
                position_code=resolved_position_code,
                group_code=resolved_group_code,
                offer_code=resolved_offer_code,
                sort_order=position_sort_order,
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
        "publish_version": resolved_publish_version,
        "group_code": resolved_group_code,
        "offer_code": resolved_offer_code,
        "position_code": resolved_position_code,
        "price_code": resolved_price_code,
        "price_cents": price_cents,
        "compare_at_price_cents": compare_at_price_cents,
    }


def test_storefront_home_returns_group_sections_and_offer_cards() -> None:
    values = _seed_home_offer()
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_published_storefront_snapshot"
    assert payload["publish_version"] == values["publish_version"]
    assert payload["group_count"] >= 1
    assert payload["section_count"] >= 1
    assert payload["offer_count"] >= 1

    groups_by_code = {group["group_code"]: group for group in payload["groups"]}
    assert groups_by_code[values["group_code"]]["group_name"] == "猫砂"
    assert groups_by_code[values["group_code"]]["group_kind"] == "category"

    sections_by_group = {section["group_code"]: section for section in payload["sections"]}
    section = sections_by_group[values["group_code"]]
    assert section["section_code"] == values["group_code"]
    assert section["title"] == "猫砂"
    assert section["display_style"] == "grid"

    offer_by_code = {offer["offer_code"]: offer for offer in section["offers"]}
    offer = offer_by_code[values["offer_code"]]
    assert offer["title"] == "豆腐猫砂 6L"
    assert offer["subtitle"] == "豆腐猫砂 6L subtitle"
    assert offer["description"] == "豆腐猫砂 6L description"
    assert offer["group_code"] == values["group_code"]
    assert offer["position_code"] == values["position_code"]
    assert offer["position_sort_order"] == 10
    assert offer["is_featured"] is True
    assert offer["price_code"] == values["price_code"]
    assert offer["price_cents"] == 1099
    assert offer["compare_at_price_cents"] == 1399
    assert offer["currency"] == "USD"
    assert offer["promotion_badge"] is None
    assert offer["sold_quantity"] is None
    assert offer["paid_customer_count"] is None
    assert offer["rating_score"] is None
    assert offer["review_count"] is None
    assert offer["review_summary"] is None
    assert offer["stock_status"] == "in_stock"
    assert "猫砂" in offer["tags"]
    assert "single" in offer["tags"]


def test_storefront_home_uses_group_and_position_order() -> None:
    publish_version = _code("pub")
    first = _seed_home_offer(
        publish_version=publish_version,
        group_name="猫粮",
        group_sort_order=10,
        title="三文鱼成猫粮 1kg",
        position_sort_order=20,
    )
    second = _seed_home_offer(
        publish_version=publish_version,
        group_name="猫砂",
        group_sort_order=20,
        title="豆腐猫砂 6L",
        position_sort_order=10,
    )
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    assert payload["publish_version"] == publish_version
    assert [group["group_code"] for group in payload["groups"]][:2] == [
        first["group_code"],
        second["group_code"],
    ]
    assert payload["sections"][0]["offers"][0]["offer_code"] == first["offer_code"]
    assert payload["sections"][1]["offers"][0]["offer_code"] == second["offer_code"]


def test_storefront_home_ignores_hidden_or_inactive_rows() -> None:
    publish_version = _code("pub")
    visible = _seed_home_offer(
        publish_version=publish_version,
        group_name="可见分组",
        title="可见商品",
    )
    hidden_group = _seed_home_offer(
        publish_version=publish_version,
        group_name="隐藏分组",
        title="隐藏分组商品",
        group_display_status="hidden",
    )
    inactive_position = _seed_home_offer(
        publish_version=publish_version,
        group_name="位置停用分组",
        title="位置停用商品",
        position_is_active=False,
    )
    inactive_price = _seed_home_offer(
        publish_version=publish_version,
        group_name="价格停用分组",
        title="价格停用商品",
        price_is_active=False,
    )
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    all_offer_codes = {
        offer["offer_code"] for section in payload["sections"] for offer in section["offers"]
    }

    assert visible["offer_code"] in all_offer_codes
    assert hidden_group["offer_code"] not in all_offer_codes
    assert inactive_position["offer_code"] not in all_offer_codes
    assert inactive_price["offer_code"] not in all_offer_codes


def test_storefront_home_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200


def test_storefront_home_does_not_depend_on_catalog_domain() -> None:
    repo_text = open("app/domains/storefront/repos/home_repo.py", encoding="utf-8").read()
    service_text = open(
        "app/domains/storefront/services/home_service.py",
        encoding="utf-8",
    ).read()

    forbidden_tokens = [
        "app.domains.catalog",
        "CatalogProduct",
        "CatalogProductsResponse",
        "list_catalog_products",
        "d2c_published_products",
        "d2c_published_skus",
        "d2c_published_prices",
    ]

    for token in forbidden_tokens:
        assert token not in repo_text
        assert token not in service_text
