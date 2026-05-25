from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedGroup,
    PublishedOffer,
    PublishedOfferComponent,
    PublishedOfferPosition,
    PublishedOfferPrice,
    PublishedPromotionRule,
    PublishedPromotionTarget,
    PublishedStorefrontSection,
    PublishedStorefrontSectionLayout,
    PublishedStorefrontSectionPosition,
    PublishSyncRun,
)
from scripts.published.sync_published import sync_published_scope


@pytest.fixture()
def session() -> Session:
    settings = load_settings()
    session_factory = get_session_factory(settings.test_database_url)
    with session_factory() as db_session:
        yield db_session


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def _published_at() -> str:
    return datetime.now(UTC).isoformat()


def _snapshot_payload(publish_version: str) -> dict[str, dict[str, Any]]:
    group_code = _code("GROUP")
    offer_code = _code("OFFER")
    promotion_code = _code("PROMO")
    coupon_code = _code("COUPON")

    return {
        "/backoffice/read/v1/published/snapshot/groups": {
            "publish_version": publish_version,
            "count": 1,
            "groups": [
                {
                    "publish_version": publish_version,
                    "group_code": group_code,
                    "group_name": "猫粮",
                    "group_kind": "category",
                    "description": None,
                    "image_url": None,
                    "sort_order": 10,
                    "display_status": "visible",
                    "is_active": True,
                    "published_at": _published_at(),
                    "source_group_id": 1,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/offers": {
            "publish_version": publish_version,
            "count": 1,
            "offers": [
                {
                    "publish_version": publish_version,
                    "offer_code": offer_code,
                    "offer_type": "single",
                    "title": "AKT 猫粮 1 袋",
                    "subtitle": "适合成猫",
                    "description": "pytest offer",
                    "image_url": "https://example.test/offer.png",
                    "display_status": "visible",
                    "sell_status": "sellable",
                    "published_at": _published_at(),
                    "source_offer_id": 2,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/offer-components": {
            "publish_version": publish_version,
            "count": 1,
            "components": [
                {
                    "publish_version": publish_version,
                    "offer_code": offer_code,
                    "component_no": 1,
                    "pms_item_id": 1001,
                    "pms_sku": "PMS-CAT-FOOD",
                    "pms_sku_code_id": 2001,
                    "sku_code": "CAT-FOOD-1KG",
                    "pms_item_uom_id": 3001,
                    "uom_code": "bag",
                    "uom_name": "袋",
                    "pms_barcode_id": 4001,
                    "barcode": "6900000000001",
                    "quantity": "1.000000",
                    "component_role": "primary",
                    "sort_order": 10,
                    "required": True,
                    "published_at": _published_at(),
                    "source_component_id": 3,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/offer-prices": {
            "publish_version": publish_version,
            "count": 1,
            "prices": [
                {
                    "publish_version": publish_version,
                    "offer_code": offer_code,
                    "price_code": _code("PRICE"),
                    "channel": "storefront",
                    "currency": "USD",
                    "price_cents": 1999,
                    "compare_at_price_cents": 2199,
                    "effective_from": None,
                    "effective_until": None,
                    "is_active": True,
                    "priority": 10,
                    "published_at": _published_at(),
                    "source_price_id": 4,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/offer-positions": {
            "publish_version": publish_version,
            "count": 1,
            "positions": [
                {
                    "publish_version": publish_version,
                    "position_code": _code("POS"),
                    "group_code": group_code,
                    "offer_code": offer_code,
                    "sort_order": 1,
                    "position_source": "manual",
                    "is_featured": True,
                    "visible_from": None,
                    "visible_until": None,
                    "is_active": True,
                    "published_at": _published_at(),
                    "source_position_id": 5,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/storefront-sections": {
            "publish_version": publish_version,
            "count": 1,
            "sections": [
                {
                    "publish_version": publish_version,
                    "section_code": _code("SECTION"),
                    "section_type": "offer_shelf",
                    "group_code": group_code,
                    "title": "猫粮精选",
                    "subtitle": "精选主粮",
                    "description": "pytest section",
                    "sort_order": 10,
                    "display_status": "visible",
                    "is_active": True,
                    "published_at": _published_at(),
                    "source_section_id": 9,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/storefront-section-layouts": {
            "publish_version": publish_version,
            "count": 1,
            "layouts": [
                {
                    "publish_version": publish_version,
                    "section_code": _code("SECTION"),
                    "display_type": "product_grid",
                    "columns_desktop": 4,
                    "columns_tablet": 2,
                    "columns_mobile": 1,
                    "card_size": "standard",
                    "image_ratio": "1:1",
                    "show_promotion_badge": True,
                    "show_sales_summary": True,
                    "show_review_summary": True,
                    "show_compare_price": True,
                    "show_quantity_stepper": True,
                    "max_items": 12,
                    "published_at": _published_at(),
                    "source_layout_id": 10,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/storefront-section-positions": {
            "publish_version": publish_version,
            "count": 1,
            "positions": [
                {
                    "publish_version": publish_version,
                    "section_code": _code("SECTION"),
                    "position_code": _code("SEC-POS"),
                    "offer_code": offer_code,
                    "sort_order": 1,
                    "position_type": "manual",
                    "is_featured": True,
                    "visible_from": None,
                    "visible_until": None,
                    "is_active": True,
                    "published_at": _published_at(),
                    "source_position_id": 11,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/promotion-rules": {
            "publish_version": publish_version,
            "count": 1,
            "promotion_rules": [
                {
                    "publish_version": publish_version,
                    "promotion_code": promotion_code,
                    "promotion_name": "周末九折",
                    "description": "pytest promotion",
                    "promotion_type": "group_discount",
                    "discount_type": "percentage",
                    "discount_value": 10,
                    "threshold_amount_cents": None,
                    "max_discount_cents": None,
                    "currency": "USD",
                    "starts_at": None,
                    "ends_at": None,
                    "priority": 10,
                    "stackable": False,
                    "is_active": True,
                    "display_badge": "周末9折",
                    "published_at": _published_at(),
                    "source_promotion_rule_id": 6,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/promotion-targets": {
            "publish_version": publish_version,
            "count": 1,
            "promotion_targets": [
                {
                    "publish_version": publish_version,
                    "promotion_code": promotion_code,
                    "target_type": "group",
                    "target_id": None,
                    "target_code": group_code,
                    "published_at": _published_at(),
                    "source_target_id": 7,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
        "/backoffice/read/v1/published/snapshot/coupons": {
            "publish_version": publish_version,
            "count": 1,
            "coupons": [
                {
                    "publish_version": publish_version,
                    "coupon_code": coupon_code,
                    "coupon_name": "新人券",
                    "promotion_code": promotion_code,
                    "coupon_type": "public_code",
                    "total_limit": 100,
                    "per_customer_limit": 1,
                    "starts_at": None,
                    "ends_at": None,
                    "is_active": True,
                    "published_at": _published_at(),
                    "source_coupon_id": 8,
                    "raw_payload": {"source": "test"},
                }
            ],
        },
    }


def test_snapshot_all_sync_pulls_terminal_runtime_rows(session: Session) -> None:
    publish_version = _code("PUB")
    payload_by_endpoint = _snapshot_payload(publish_version)

    for model in (
        PublishedCoupon,
        PublishedPromotionTarget,
        PublishedStorefrontSectionPosition,
        PublishedStorefrontSectionLayout,
        PublishedStorefrontSection,
        PublishedPromotionRule,
        PublishedOfferPosition,
        PublishedStorefrontSection,
        PublishedStorefrontSectionLayout,
        PublishedOfferPrice,
        PublishedOfferComponent,
        PublishedOffer,
        PublishedGroup,
        PublishSyncRun,
    ):
        session.execute(delete(model))
    session.commit()

    def fake_fetcher(
        _base_url: str,
        endpoint: str,
        _service_client: str,
        _publish_version: str | None,
    ) -> dict[str, Any]:
        return payload_by_endpoint[endpoint]

    sync_run = sync_published_scope(
        session,
        scope="snapshot-all",
        base_url="http://backoffice.test",
        service_client="d2c-service",
        publish_version=publish_version,
        requested_by="pytest",
        fetcher=fake_fetcher,
    )

    assert sync_run.status == "success"
    assert sync_run.publish_version == publish_version
    assert sync_run.rows_fetched == 11
    assert sync_run.rows_upserted == 11

    assert session.scalar(select(PublishedGroup)) is not None
    assert session.scalar(select(PublishedOffer)) is not None
    assert session.scalar(select(PublishedOfferComponent)) is not None
    assert session.scalar(select(PublishedOfferPrice)) is not None
    assert session.scalar(select(PublishedOfferPosition)) is not None
    assert session.scalar(select(PublishedStorefrontSectionLayout)) is not None
    assert session.scalar(select(PublishedStorefrontSectionPosition)) is not None
    assert session.scalar(select(PublishedStorefrontSection)) is not None
    assert session.scalar(select(PublishedPromotionRule)) is not None
    assert session.scalar(select(PublishedPromotionTarget)) is not None
    assert session.scalar(select(PublishedCoupon)) is not None


def test_snapshot_single_scope_sync_is_supported(session: Session) -> None:
    publish_version = _code("PUB")
    payload_by_endpoint = _snapshot_payload(publish_version)

    session.execute(delete(PublishedGroup))
    session.commit()

    def fake_fetcher(
        _base_url: str,
        endpoint: str,
        _service_client: str,
        _publish_version: str | None,
    ) -> dict[str, Any]:
        return payload_by_endpoint[endpoint]

    sync_run = sync_published_scope(
        session,
        scope="snapshot-groups",
        base_url="http://backoffice.test",
        service_client="d2c-service",
        publish_version=publish_version,
        requested_by="pytest",
        fetcher=fake_fetcher,
    )

    assert sync_run.status == "success"
    assert sync_run.rows_fetched == 1
    assert session.scalar(select(PublishedGroup)) is not None
