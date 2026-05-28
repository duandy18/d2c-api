from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import PublishedOffer, PublishedOfferPrice
from app.domains.site_config.models import (
    StorefrontPage,
    StorefrontPageSlot,
    StorefrontSite,
    StorefrontSlotOfferPosition,
)
from app.main import app


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].lower()}"


def _future_now() -> datetime:
    return datetime(2099, 1, 1, 0, 0, 0, tzinfo=UTC)


def _session_factory():
    settings = load_settings()
    return get_session_factory(settings.database_url)


def _home_product_grid_slot_id() -> int:
    session_factory = _session_factory()

    with session_factory() as session:
        slot_id = session.scalar(
            select(StorefrontPageSlot.id)
            .join(StorefrontPage, StorefrontPage.id == StorefrontPageSlot.page_id)
            .join(StorefrontSite, StorefrontSite.id == StorefrontPage.site_id)
            .where(StorefrontSite.site_code == "default")
            .where(StorefrontPage.page_code == "home")
            .where(StorefrontPageSlot.slot_code == "product_grid.list")
        )

    assert slot_id is not None
    return int(slot_id)


def _replace_product_grid_positions(*, offers: list[dict[str, object]]) -> list[dict[str, object]]:
    session_factory = _session_factory()
    slot_id = _home_product_grid_slot_id()
    publish_version = _code("pub")
    now = _future_now()
    seeded: list[dict[str, object]] = []

    with session_factory() as session:
        session.execute(
            delete(StorefrontSlotOfferPosition).where(
                StorefrontSlotOfferPosition.slot_id == slot_id
            )
        )

        for index, offer in enumerate(offers, start=1):
            offer_code = str(offer.get("offer_code") or _code("offer"))
            title = str(offer.get("title") or f"测试商品 {index}")
            price_cents = int(offer.get("price_cents") or 1099)
            compare_at_price_cents = offer.get("compare_at_price_cents", 1399)
            position_code = str(offer.get("position_code") or _code("home-pos"))
            position_sort_order = int(offer.get("position_sort_order") or index * 10)
            position_is_active = bool(offer.get("position_is_active", True))
            offer_display_status = str(offer.get("offer_display_status") or "visible")
            offer_sell_status = str(offer.get("offer_sell_status") or "sellable")
            price_is_active = bool(offer.get("price_is_active", True))
            price_code = str(offer.get("price_code") or _code("price"))

            session.add(
                PublishedOffer(
                    publish_version=publish_version,
                    offer_code=offer_code,
                    offer_type=str(offer.get("offer_type") or "single"),
                    title=title,
                    subtitle=f"{title} subtitle",
                    description=f"{title} description",
                    image_url="https://example.test/offer.png",
                    display_status=offer_display_status,
                    sell_status=offer_sell_status,
                    source_offer_id=index,
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
                    compare_at_price_cents=(
                        int(compare_at_price_cents)
                        if compare_at_price_cents is not None
                        else None
                    ),
                    effective_from=None,
                    effective_until=None,
                    is_active=price_is_active,
                    priority=10,
                    source_price_id=index,
                    raw_payload={"source": "pytest"},
                    published_at=now,
                )
            )
            session.add(
                StorefrontSlotOfferPosition(
                    slot_id=slot_id,
                    position_code=position_code,
                    offer_code=offer_code,
                    position_type=str(offer.get("position_type") or "manual"),
                    is_featured=bool(offer.get("is_featured", True)),
                    sort_order=position_sort_order,
                    is_active=position_is_active,
                    visible_from=None,
                    visible_until=None,
                )
            )

            seeded.append(
                {
                    "publish_version": publish_version,
                    "offer_code": offer_code,
                    "title": title,
                    "price_code": price_code,
                    "price_cents": price_cents,
                    "compare_at_price_cents": (
                        int(compare_at_price_cents)
                        if compare_at_price_cents is not None
                        else None
                    ),
                    "position_code": position_code,
                    "position_sort_order": position_sort_order,
                }
            )

        session.commit()

    return seeded


def _slot_by_code(payload: dict, slot_code: str) -> dict:
    page = payload["page"]
    assert page is not None
    slots = {slot["slot_code"]: slot for slot in page["slots"]}
    return slots[slot_code]


def _product_grid_offers(payload: dict) -> list[dict]:
    return _slot_by_code(payload, "product_grid.list")["offers"]


def test_storefront_home_returns_slot_first_page_slot_offer_protocol() -> None:
    seeded = _replace_product_grid_positions(
        offers=[
            {
                "offer_code": _code("offer"),
                "title": "豆腐猫砂 6L",
                "price_cents": 1099,
                "compare_at_price_cents": 1399,
                "position_code": _code("home-pos"),
            }
        ]
    )[0]
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_storefront_site_config"
    assert "publish_version" not in payload
    assert payload["slot_count"] >= 1
    assert payload["item_count"] >= 1
    assert payload["offer_count"] >= 1
    assert payload["site"]["site_code"] == "default"

    page = payload["page"]
    assert page["page_code"] == "home"
    assert page["page_type"] == "home"
    assert page["route_path"] == "/"
    assert "regions" not in page
    assert "blocks" not in page

    hero_slot = _slot_by_code(payload, "hero.title")
    assert hero_slot["slot_type"] == "hero"
    assert hero_slot["slot_group"] == "main"
    assert hero_slot["content"]["title"]

    product_slot = _slot_by_code(payload, "product_grid.list")
    assert product_slot["slot_type"] == "product_grid"
    assert product_slot["slot_group"] == "commerce"

    offers = product_slot["offers"]
    assert len(offers) == 1

    position = offers[0]
    assert position["position_code"] == seeded["position_code"]
    assert position["offer_code"] == seeded["offer_code"]
    assert position["position_type"] == "manual"
    assert position["is_featured"] is True

    offer = position["offer"]
    assert offer["offer_code"] == seeded["offer_code"]
    assert offer["title"] == "豆腐猫砂 6L"
    assert offer["subtitle"] == "豆腐猫砂 6L subtitle"
    assert offer["description"] == "豆腐猫砂 6L description"
    assert offer["price_code"] == seeded["price_code"]
    assert offer["price_cents"] == 1099
    assert offer["compare_at_price_cents"] == 1399
    assert offer["currency"] == "USD"
    assert offer["stock_status"] == "in_stock"
    assert offer["sell_status"] == "sellable"


def test_storefront_home_uses_slot_offer_position_order() -> None:
    second = {
        "offer_code": _code("offer"),
        "title": "豆腐猫砂 6L",
        "position_code": _code("home-pos"),
        "position_sort_order": 20,
    }
    first = {
        "offer_code": _code("offer"),
        "title": "三文鱼成猫粮 1kg",
        "position_code": _code("home-pos"),
        "position_sort_order": 10,
    }
    seeded = _replace_product_grid_positions(offers=[second, first])
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    offers = _product_grid_offers(payload)

    assert [position["offer"]["offer_code"] for position in offers] == [
        seeded[1]["offer_code"],
        seeded[0]["offer_code"],
    ]


def test_storefront_home_ignores_inactive_or_unhydrated_slot_offer_positions() -> None:
    visible = {
        "offer_code": _code("offer"),
        "title": "可见商品",
        "position_code": _code("home-pos"),
        "position_sort_order": 10,
    }
    inactive_position = {
        "offer_code": _code("offer"),
        "title": "位置停用商品",
        "position_code": _code("home-pos"),
        "position_sort_order": 20,
        "position_is_active": False,
    }
    inactive_price = {
        "offer_code": _code("offer"),
        "title": "价格停用商品",
        "position_code": _code("home-pos"),
        "position_sort_order": 30,
        "price_is_active": False,
    }
    hidden_offer = {
        "offer_code": _code("offer"),
        "title": "隐藏商品",
        "position_code": _code("home-pos"),
        "position_sort_order": 40,
        "offer_display_status": "hidden",
    }
    seeded = _replace_product_grid_positions(
        offers=[visible, inactive_position, inactive_price, hidden_offer]
    )
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    all_offer_codes = {
        position["offer"]["offer_code"]
        for position in _product_grid_offers(payload)
    }

    assert seeded[0]["offer_code"] in all_offer_codes
    assert seeded[1]["offer_code"] not in all_offer_codes
    assert seeded[2]["offer_code"] not in all_offer_codes
    assert seeded[3]["offer_code"] not in all_offer_codes


def test_storefront_home_route_is_registered() -> None:
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200


def test_storefront_home_does_not_expose_old_region_block_contract() -> None:
    client = TestClient(app)

    response = client.get("/storefront/home")

    assert response.status_code == 200

    payload = response.json()
    assert payload["data_source"] == "d2c_storefront_site_config"
    assert "publish_version" not in payload
    assert "region_count" not in payload
    assert "block_count" not in payload

    page = payload["page"]
    assert page is not None
    assert "slots" in page
    assert "regions" not in page
    assert "blocks" not in page


def test_storefront_home_no_longer_depends_on_client_presentation_snapshot_paths() -> None:
    route_text = open("app/api/routes/storefront/home.py", encoding="utf-8").read()
    contract_text = open(
        "app/domains/site_config/contracts/storefront_home_contract.py",
        encoding="utf-8",
    ).read()
    service_text = open(
        "app/domains/site_config/services/storefront_home_service.py",
        encoding="utf-8",
    ).read()

    forbidden_route_tokens = [
        "app.domains.storefront.services.home_service",
        "app.domains.storefront.contracts.home_contract",
    ]

    for token in forbidden_route_tokens:
        assert token not in route_text

    forbidden_contract_tokens = [
        "d2c_published_client_presentation_snapshot",
        "StorefrontHomeRegion",
        "StorefrontHomeBlock",
        "regions:",
        "blocks:",
        "publish_version",
    ]

    for token in forbidden_contract_tokens:
        assert token not in contract_text

    forbidden_service_tokens = [
        "PublishedClientPage",
        "PublishedClientRegion",
        "PublishedStorefrontSection",
        "PublishedStorefrontSectionPosition",
        "list_home_regions",
        "list_home_sections",
        "build_region",
        "build_block",
    ]

    for token in forbidden_service_tokens:
        assert token not in service_text
