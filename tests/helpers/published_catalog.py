"""Published catalog seed helpers for storefront runtime tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

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
)


def _publish_version() -> str:
    return f"TEST-PUB-{uuid4().hex[:16].upper()}"


def seed_published_offer_catalog_item(
    *,
    offer_code: str,
    sku_code: str,
    display_name: str,
    pms_item_id: int | None = 1001,
    pms_sku: str | None = "PMS-CAT-FOOD-SALMON",
    group_code: str = "cat_food",
    group_name: str = "猫粮",
    sales_unit_code: str = "bag",
    sales_unit_name: str = "袋",
    barcode: str | None = "6900000000000",
    price_code: str | None = None,
    price_cents: int = 1899,
    compare_at_price_cents: int | None = 2299,
    currency: str = "USD",
    price_is_active: bool = True,
    position_is_active: bool = True,
    source_offer_id: int | None = 501,
    source_component_id: int | None = 601,
    source_price_id: int | None = 701,
    source_position_id: int | None = 801,
) -> dict[str, str | int | None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    publish_version = _publish_version()
    now = datetime.now(UTC)
    resolved_price_code = price_code or f"price-{offer_code}"
    position_code = f"pos-{offer_code}-{uuid4().hex[:8]}"

    with session_factory() as session:
        session.add(
            PublishedGroup(
                publish_version=publish_version,
                group_code=group_code,
                group_name=group_name,
                group_kind="category",
                description=f"{group_name} published test group",
                image_url=None,
                sort_order=10,
                display_status="visible",
                is_active=True,
                source_group_id=source_position_id,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOffer(
                publish_version=publish_version,
                offer_code=offer_code,
                offer_type="single",
                title=display_name,
                subtitle=f"{display_name} subtitle",
                description=f"{display_name} published test item",
                image_url=None,
                display_status="visible",
                sell_status="sellable",
                source_offer_id=source_offer_id,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOfferComponent(
                publish_version=publish_version,
                offer_code=offer_code,
                component_no=1,
                pms_item_id=pms_item_id or 0,
                pms_sku=pms_sku or "",
                pms_sku_code_id=source_component_id or 0,
                sku_code=sku_code,
                pms_item_uom_id=source_component_id or 0,
                uom_code=sales_unit_code,
                uom_name=sales_unit_name,
                pms_barcode_id=source_component_id,
                barcode=barcode,
                quantity=Decimal("1.000000"),
                component_role="primary",
                sort_order=10,
                required=True,
                source_component_id=source_component_id,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedOfferPrice(
                publish_version=publish_version,
                offer_code=offer_code,
                price_code=resolved_price_code,
                channel="storefront",
                currency=currency,
                price_cents=price_cents,
                compare_at_price_cents=compare_at_price_cents,
                effective_from=None,
                effective_until=None,
                is_active=price_is_active,
                priority=10,
                source_price_id=source_price_id,
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
                sort_order=10,
                position_source="manual",
                is_featured=True,
                visible_from=None,
                visible_until=None,
                is_active=position_is_active,
                source_position_id=source_position_id,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.commit()

    return {
        "publish_version": publish_version,
        "offer_code": offer_code,
        "sku_code": sku_code,
        "display_name": display_name,
        "pms_item_id": pms_item_id,
        "pms_sku": pms_sku,
        "group_code": group_code,
        "group_name": group_name,
        "sales_unit_code": sales_unit_code,
        "sales_unit_name": sales_unit_name,
        "barcode": barcode,
        "price_code": resolved_price_code,
        "price_cents": price_cents,
        "compare_at_price_cents": compare_at_price_cents,
        "source_offer_id": source_offer_id,
        "source_component_id": source_component_id,
        "source_price_id": source_price_id,
        "source_position_id": source_position_id,
    }


def seed_default_published_catalog() -> None:
    seed_published_offer_catalog_item(
        offer_code="offer-cat-food-salmon-001",
        sku_code="CAT-FOOD-SALMON-1KG",
        display_name="三文鱼成猫粮 1kg",
        price_cents=1899,
    )
    seed_published_offer_catalog_item(
        offer_code="offer-cat-litter-tofu-001",
        sku_code="CAT-LITTER-TOFU-6L",
        display_name="豆腐猫砂 6L",
        pms_item_id=1002,
        pms_sku="PMS-CAT-LITTER-TOFU",
        group_code="cat_litter",
        group_name="猫砂",
        sales_unit_code="box",
        sales_unit_name="箱",
        barcode="6900000000001",
        price_cents=1099,
        compare_at_price_cents=1399,
        source_offer_id=502,
        source_component_id=602,
        source_price_id=702,
        source_position_id=802,
    )


def seed_published_promotion(
    *,
    promotion_code: str,
    publish_version: str | None = None,
    promotion_name: str = "测试全店折扣",
    promotion_type: str = "store_campaign",
    discount_type: str = "percentage",
    discount_value: int = 10,
    scope_type: str = "all_store",
    min_order_amount_cents: int | None = None,
    max_discount_cents: int | None = None,
    currency: str = "USD",
    is_active: bool = True,
) -> dict[str, str | int | bool | None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    resolved_publish_version = publish_version or _publish_version()
    now = datetime.now(UTC)

    with session_factory() as session:
        session.add(
            PublishedPromotionRule(
                publish_version=resolved_publish_version,
                promotion_code=promotion_code,
                promotion_name=promotion_name,
                description=None,
                promotion_type=promotion_type,
                discount_type=discount_type,
                discount_value=discount_value,
                threshold_amount_cents=min_order_amount_cents,
                max_discount_cents=max_discount_cents,
                currency=currency,
                starts_at=None,
                ends_at=None,
                priority=10,
                stackable=False,
                is_active=is_active,
                display_badge=None,
                source_promotion_rule_id=None,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.add(
            PublishedPromotionTarget(
                publish_version=resolved_publish_version,
                promotion_code=promotion_code,
                target_type=scope_type,
                target_id=None,
                target_code=None,
                source_target_id=None,
                raw_payload={"source": "pytest"},
                published_at=now,
            )
        )
        session.commit()

    return {
        "publish_version": resolved_publish_version,
        "promotion_code": promotion_code,
        "promotion_name": promotion_name,
        "promotion_type": promotion_type,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "scope_type": scope_type,
        "currency": currency,
        "is_active": is_active,
    }


def seed_published_coupon(
    *,
    publish_version: str,
    coupon_code: str,
    promotion_code: str,
    coupon_name: str = "Checkout Coupon",
    coupon_type: str = "public_code",
    total_limit: int | None = 100,
    per_customer_limit: int | None = 1,
    is_active: bool = True,
) -> dict[str, str | int | bool | None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)
    now = datetime.now(UTC)

    with session_factory() as session:
        session.add(
            PublishedCoupon(
                publish_version=publish_version,
                coupon_code=coupon_code,
                coupon_name=coupon_name,
                promotion_code=promotion_code,
                coupon_type=coupon_type,
                total_limit=total_limit,
                per_customer_limit=per_customer_limit,
                starts_at=None,
                ends_at=None,
                is_active=is_active,
                published_at=now,
                source_coupon_id=None,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
            )
        )
        session.commit()

    return {
        "publish_version": publish_version,
        "coupon_code": coupon_code,
        "coupon_name": coupon_name,
        "promotion_code": promotion_code,
        "coupon_type": coupon_type,
        "total_limit": total_limit,
        "per_customer_limit": per_customer_limit,
        "is_active": is_active,
    }
