from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPrice,
    PublishedStorefrontSection,
    PublishedStorefrontSectionLayout,
    PublishedStorefrontSectionPosition,
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
    section_code: str | None = None,
    section_title: str = "猫砂主推",
    section_type: str = "offer_shelf",
    section_sort_order: int = 5,
    section_display_status: str = "visible",
    section_is_active: bool = True,
    position_code: str | None = None,
    position_sort_order: int = 10,
    position_is_active: bool = True,
    price_code: str | None = None,
    price_cents: int = 1099,
    compare_at_price_cents: int | None = 1399,
    price_is_active: bool = True,
    layout_display_type: str = "featured_grid",
    layout_columns_desktop: int = 2,
) -> dict[str, str | int | None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    resolved_publish_version = publish_version or _code("pub")
    resolved_group_code = group_code or _code("group")
    resolved_offer_code = offer_code or _code("offer")
    resolved_section_code = section_code or _code("section")
    resolved_position_code = position_code or _code("sec-pos")
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
            PublishedStorefrontSection(
                publish_version=resolved_publish_version,
                section_code=resolved_section_code,
                section_type=section_type,
                group_code=resolved_group_code,
                title=section_title,
                subtitle="section subtitle",
                description="section description",
                sort_order=section_sort_order,
                display_status=section_display_status,
                is_active=section_is_active,
                source_section_id=2,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedStorefrontSectionLayout(
                publish_version=resolved_publish_version,
                section_code=resolved_section_code,
                display_type=layout_display_type,
                columns_desktop=layout_columns_desktop,
                columns_tablet=2,
                columns_mobile=1,
                card_size="large",
                image_ratio="4:3",
                show_promotion_badge=True,
                show_sales_summary=True,
                show_review_summary=True,
                show_compare_price=True,
                show_quantity_stepper=True,
                max_items=8,
                source_layout_id=3,
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
                source_offer_id=4,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedStorefrontSectionPosition(
                publish_version=resolved_publish_version,
                section_code=resolved_section_code,
                position_code=resolved_position_code,
                offer_code=resolved_offer_code,
                sort_order=position_sort_order,
                position_type="manual",
                is_featured=True,
                visible_from=None,
                visible_until=None,
                is_active=position_is_active,
                source_position_id=5,
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
                source_price_id=6,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.commit()

    return {
        "publish_version": resolved_publish_version,
        "group_code": resolved_group_code,
        "offer_code": resolved_offer_code,
        "section_code": resolved_section_code,
        "position_code": resolved_position_code,
        "price_code": resolved_price_code,
        "price_cents": price_cents,
        "compare_at_price_cents": compare_at_price_cents,
    }


def test_storefront_home_returns_section_position_offer_cards() -> None:
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

    sections_by_code = {section["section_code"]: section for section in payload["sections"]}
    section = sections_by_code[values["section_code"]]
    assert section["section_type"] == "offer_shelf"
    assert section["group_code"] == values["group_code"]
    assert section["title"] == "猫砂主推"
    assert section["display_style"] == "grid"
    assert section["layout"]["display_type"] == "featured_grid"
    assert section["layout"]["columns_desktop"] == 2

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
    assert offer["stock_status"] == "in_stock"
    assert "猫砂" in offer["tags"]
    assert "single" in offer["tags"]


def test_storefront_home_uses_section_and_section_position_order() -> None:
    publish_version = _code("pub")
    first = _seed_home_offer(
        publish_version=publish_version,
        group_name="猫粮",
        title="三文鱼成猫粮 1kg",
        section_title="猫粮主推",
        section_sort_order=10,
        position_sort_order=20,
    )
    second = _seed_home_offer(
        publish_version=publish_version,
        group_name="猫砂",
        title="豆腐猫砂 6L",
        section_title="猫砂主推",
        section_sort_order=20,
        position_sort_order=10,
    )
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    assert payload["publish_version"] == publish_version
    assert [section["section_code"] for section in payload["sections"]][:2] == [
        first["section_code"],
        second["section_code"],
    ]
    assert payload["sections"][0]["offers"][0]["offer_code"] == first["offer_code"]
    assert payload["sections"][1]["offers"][0]["offer_code"] == second["offer_code"]


def test_storefront_home_ignores_hidden_or_inactive_terminal_rows() -> None:
    publish_version = _code("pub")
    visible = _seed_home_offer(
        publish_version=publish_version,
        group_name="可见分组",
        title="可见商品",
    )
    hidden_section = _seed_home_offer(
        publish_version=publish_version,
        group_name="隐藏货架分组",
        title="隐藏货架商品",
        section_display_status="hidden",
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
    assert hidden_section["offer_code"] not in all_offer_codes
    assert inactive_position["offer_code"] not in all_offer_codes
    assert inactive_price["offer_code"] not in all_offer_codes


def test_storefront_home_does_not_fallback_to_group_offer_positions() -> None:
    values = _seed_home_offer()
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    sections_by_code = {section["section_code"]: section for section in payload["sections"]}

    assert values["section_code"] in sections_by_code
    assert values["group_code"] not in sections_by_code


def test_storefront_home_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200


def test_storefront_home_does_not_depend_on_catalog_or_offer_position_paths() -> None:
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
        "PublishedOfferPosition",
        "_build_fallback_sections",
        "offers_by_group",
        "PublishedOfferPosition.group_code",
        "PublishedOfferPosition.offer_code",
    ]

    for token in forbidden_tokens:
        assert token not in repo_text
        assert token not in service_text
