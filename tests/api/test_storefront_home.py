from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedClientActionPolicy,
    PublishedClientDataBinding,
    PublishedClientPage,
    PublishedClientRegion,
    PublishedClientTrackingPolicy,
    PublishedClientVisibilityRule,
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
    page_code: str = "home",
    page_title: str = "首页",
    region_code: str | None = None,
    region_type: str = "main",
    region_title: str = "首页主体",
    region_sort_order: int = 10,
    region_allowed_block_types: list[str] | None = None,
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
    resolved_region_code = region_code or _code("home-main")
    resolved_offer_code = offer_code or _code("offer")
    resolved_section_code = section_code or _code("section")
    resolved_position_code = position_code or _code("sec-pos")
    resolved_price_code = price_code or _code("price")
    resolved_allowed_block_types = region_allowed_block_types or [section_type]
    now = datetime.now(UTC)

    data_binding_code = _code("binding")
    visibility_rule_code = _code("visibility")
    action_policy_code = _code("action")
    tracking_policy_code = _code("tracking")

    with session_factory() as session:
        page_exists = session.scalar(
            select(PublishedClientPage).where(
                PublishedClientPage.publish_version == resolved_publish_version,
                PublishedClientPage.page_code == page_code,
            )
        )
        if page_exists is None:
            session.add(
                PublishedClientPage(
                    publish_version=resolved_publish_version,
                    page_code=page_code,
                    page_type="home",
                    route_path="/",
                    title=page_title,
                    description=f"{page_title} description",
                    seo_title=f"{page_title} seo",
                    seo_description=f"{page_title} seo description",
                    sort_order=10,
                    display_status="visible",
                    is_active=True,
                    published_at=now,
                    source_page_id=1,
                    raw_payload={"source": "pytest"},
                )
            )

        region_exists = session.scalar(
            select(PublishedClientRegion).where(
                PublishedClientRegion.publish_version == resolved_publish_version,
                PublishedClientRegion.region_code == resolved_region_code,
            )
        )
        if region_exists is None:
            session.add(
                PublishedClientRegion(
                    publish_version=resolved_publish_version,
                    region_code=resolved_region_code,
                    page_code=page_code,
                    region_type=region_type,
                    title=region_title,
                    description=f"{region_title} description",
                    sort_order=region_sort_order,
                    allowed_block_types=resolved_allowed_block_types,
                    max_blocks=8,
                    is_required=True,
                    display_status="visible",
                    is_active=True,
                    published_at=now,
                    source_region_id=2,
                    raw_payload={"source": "pytest"},
                )
            )

        session.add(
            PublishedClientDataBinding(
                publish_version=resolved_publish_version,
                binding_code=data_binding_code,
                target_type="block_type",
                target_code=section_type,
                content_type="offer",
                data_source_type="section_positions",
                data_source_ref="published_section_positions",
                query_params={"section_type": section_type},
                sort_policy={"order_by": ["sort_order"]},
                result_limit=12,
                refresh_policy={"mode": "publish_snapshot"},
                is_active=True,
                published_at=now,
                source_binding_id=3,
                raw_payload={"source": "pytest"},
            )
        )
        session.add(
            PublishedClientVisibilityRule(
                publish_version=resolved_publish_version,
                rule_code=visibility_rule_code,
                target_type="block_type",
                target_code=section_type,
                client_surface_codes=["web_desktop"],
                customer_segments=["all"],
                login_state="any",
                locale=None,
                currency=None,
                visible_from=None,
                visible_until=None,
                rule_expression={"allow": True},
                priority=1,
                is_active=True,
                published_at=now,
                source_rule_id=4,
                raw_payload={"source": "pytest"},
            )
        )
        session.add(
            PublishedClientActionPolicy(
                publish_version=resolved_publish_version,
                policy_code=action_policy_code,
                target_type="block_type",
                target_code=section_type,
                action_type="add_to_cart",
                label="加入购物车",
                target_url=None,
                target_page_code=None,
                target_ref="offer_code",
                open_mode="same",
                action_payload={"param": "offer_code"},
                is_active=True,
                published_at=now,
                source_policy_id=5,
                raw_payload={"source": "pytest"},
            )
        )
        session.add(
            PublishedClientTrackingPolicy(
                publish_version=resolved_publish_version,
                policy_code=tracking_policy_code,
                target_type="block_type",
                target_code=section_type,
                event_name="add_to_cart",
                event_type="conversion",
                event_trigger="action_success",
                tracking_params={"include": ["offer_code", "quantity"]},
                is_required=True,
                is_active=True,
                published_at=now,
                source_policy_id=6,
                raw_payload={"source": "pytest"},
            )
        )
        session.add(
            PublishedStorefrontSection(
                publish_version=resolved_publish_version,
                section_code=resolved_section_code,
                section_type=section_type,
                group_code=None,
                title=section_title,
                subtitle="section subtitle",
                description="section description",
                sort_order=section_sort_order,
                display_status=section_display_status,
                is_active=section_is_active,
                source_section_id=7,
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
                source_layout_id=8,
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
                source_offer_id=9,
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
                source_position_id=10,
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
                source_price_id=11,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.commit()

    return {
        "publish_version": resolved_publish_version,
        "page_code": page_code,
        "region_code": resolved_region_code,
        "offer_code": resolved_offer_code,
        "section_code": resolved_section_code,
        "position_code": resolved_position_code,
        "price_code": resolved_price_code,
        "price_cents": price_cents,
        "compare_at_price_cents": compare_at_price_cents,
        "data_binding_code": data_binding_code,
        "visibility_rule_code": visibility_rule_code,
        "action_policy_code": action_policy_code,
        "tracking_policy_code": tracking_policy_code,
    }


def _home_blocks(payload: dict) -> list[dict]:
    page = payload["page"]
    assert page is not None
    return [block for region in page["regions"] for block in region["blocks"]]


def _home_positions(payload: dict) -> list[dict]:
    return [position for block in _home_blocks(payload) for position in block["positions"]]


def test_storefront_home_returns_page_region_block_position_offer_protocol() -> None:
    values = _seed_home_offer()
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_published_client_presentation_snapshot"
    assert payload["publish_version"] == values["publish_version"]
    assert payload["page_code"] == "home"
    assert payload["surface_code"] == "web_desktop"
    assert payload["region_count"] >= 1
    assert payload["block_count"] >= 1
    assert payload["offer_count"] >= 1
    assert "groups" not in payload
    assert "sections" not in payload

    page = payload["page"]
    assert page["page_code"] == "home"
    assert page["page_type"] == "home"
    assert page["route_path"] == "/"

    regions_by_code = {region["region_code"]: region for region in page["regions"]}
    region = regions_by_code[values["region_code"]]
    assert region["region_type"] == "main"
    assert "offer_shelf" in region["allowed_block_types"]

    blocks_by_code = {block["block_code"]: block for block in region["blocks"]}
    block = blocks_by_code[values["section_code"]]
    assert block["block_type"] == "offer_shelf"
    assert block["title"] == "猫砂主推"
    assert block["layout"]["display_type"] == "featured_grid"
    assert block["layout"]["columns_desktop"] == 2
    assert values["data_binding_code"] in block["data_binding_codes"]
    assert values["visibility_rule_code"] in block["visibility_rule_codes"]
    assert values["action_policy_code"] in block["action_policy_codes"]
    assert values["tracking_policy_code"] in block["tracking_policy_codes"]

    positions_by_code = {position["position_code"]: position for position in block["positions"]}
    position = positions_by_code[values["position_code"]]
    assert position["offer_code"] == values["offer_code"]
    assert position["sort_order"] == 10
    assert position["position_type"] == "manual"
    assert position["is_featured"] is True

    offer = position["offer"]
    assert offer["offer_code"] == values["offer_code"]
    assert offer["title"] == "豆腐猫砂 6L"
    assert offer["subtitle"] == "豆腐猫砂 6L subtitle"
    assert offer["description"] == "豆腐猫砂 6L description"
    assert offer["price_code"] == values["price_code"]
    assert offer["price_cents"] == 1099
    assert offer["compare_at_price_cents"] == 1399
    assert offer["currency"] == "USD"
    assert offer["stock_status"] == "in_stock"
    assert "single" in offer["tags"]


def test_storefront_home_uses_region_block_and_position_order() -> None:
    publish_version = _code("pub")
    region_code = _code("home-main")
    first = _seed_home_offer(
        publish_version=publish_version,
        region_code=region_code,
        title="三文鱼成猫粮 1kg",
        section_title="猫粮主推",
        section_sort_order=10,
        position_sort_order=20,
    )
    second = _seed_home_offer(
        publish_version=publish_version,
        region_code=region_code,
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

    region = {item["region_code"]: item for item in payload["page"]["regions"]}[region_code]
    assert [block["block_code"] for block in region["blocks"]][:2] == [
        first["section_code"],
        second["section_code"],
    ]
    assert region["blocks"][0]["positions"][0]["offer"]["offer_code"] == first["offer_code"]
    assert region["blocks"][1]["positions"][0]["offer"]["offer_code"] == second["offer_code"]


def test_storefront_home_ignores_hidden_or_inactive_terminal_rows() -> None:
    publish_version = _code("pub")
    region_code = _code("home-main")
    visible = _seed_home_offer(
        publish_version=publish_version,
        region_code=region_code,
        title="可见商品",
    )
    hidden_section = _seed_home_offer(
        publish_version=publish_version,
        region_code=region_code,
        title="隐藏货架商品",
        section_display_status="hidden",
    )
    inactive_position = _seed_home_offer(
        publish_version=publish_version,
        region_code=region_code,
        title="位置停用商品",
        position_is_active=False,
    )
    inactive_price = _seed_home_offer(
        publish_version=publish_version,
        region_code=region_code,
        title="价格停用商品",
        price_is_active=False,
    )
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    all_offer_codes = {position["offer"]["offer_code"] for position in _home_positions(payload)}

    assert visible["offer_code"] in all_offer_codes
    assert hidden_section["offer_code"] not in all_offer_codes
    assert inactive_position["offer_code"] not in all_offer_codes
    assert inactive_price["offer_code"] not in all_offer_codes


def test_storefront_home_assigns_blocks_by_region_allowed_block_types() -> None:
    publish_version = _code("pub")
    shelf_region = _code("home-shelf")
    banner_region = _code("home-banner")
    shelf = _seed_home_offer(
        publish_version=publish_version,
        region_code=shelf_region,
        region_allowed_block_types=["offer_shelf"],
        section_type="offer_shelf",
        section_title="商品货架",
    )
    banner = _seed_home_offer(
        publish_version=publish_version,
        region_code=banner_region,
        region_type="hero",
        region_title="头图区域",
        region_sort_order=1,
        region_allowed_block_types=["hero_banner"],
        section_type="hero_banner",
        section_title="首页头图",
        layout_display_type="banner",
    )
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    regions_by_code = {region["region_code"]: region for region in payload["page"]["regions"]}

    assert regions_by_code[shelf_region]["blocks"][0]["block_code"] == shelf["section_code"]
    assert regions_by_code[banner_region]["blocks"][0]["block_code"] == banner["section_code"]


def test_storefront_home_does_not_fallback_to_group_offer_positions() -> None:
    values = _seed_home_offer()
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    block_codes = {block["block_code"] for block in _home_blocks(payload)}

    assert values["section_code"] in block_codes


def test_storefront_home_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200


def test_storefront_home_does_not_depend_on_catalog_group_or_offer_position_paths() -> None:
    contract_text = open(
        "app/domains/storefront/contracts/home_contract.py",
        encoding="utf-8",
    ).read()
    repo_text = open("app/domains/storefront/repos/home_repo.py", encoding="utf-8").read()
    service_text = open(
        "app/domains/storefront/services/home_service.py",
        encoding="utf-8",
    ).read()

    forbidden_dependency_tokens = [
        "app.domains.catalog",
        "CatalogProduct",
        "CatalogProductsResponse",
        "list_catalog_products",
        "d2c_published_products",
        "d2c_published_skus",
        "d2c_published_prices",
        "PublishedGroup",
        "PublishedOfferPosition",
        "_build_fallback_sections",
        "offers_by_group",
        "PublishedOfferPosition.group_code",
        "PublishedOfferPosition.offer_code",
    ]

    for token in forbidden_dependency_tokens:
        assert token not in repo_text
        assert token not in service_text

    forbidden_top_level_contract_tokens = [
        "StorefrontHomeGroup",
        "groups:",
        "sections:",
        "groups=[]",
        "sections=[]",
        '"d2c_published_storefront_snapshot"',
    ]

    for token in forbidden_top_level_contract_tokens:
        assert token not in contract_text
