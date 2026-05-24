"""Published catalog seed helpers for storefront runtime tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedPrice,
    PublishedProduct,
    PublishedPromotion,
    PublishedSku,
)


def _publish_version() -> str:
    return f"TEST-PUB-{uuid4().hex[:16].upper()}"


def seed_published_catalog_item(
    *,
    product_code: str,
    sku_code: str,
    display_name: str,
    sku_name: str | None = None,
    pms_item_id: int | None = 1001,
    pms_sku: str | None = "PMS-CAT-FOOD-SALMON",
    category_code: str = "cat_food",
    category_name: str = "猫粮",
    brand_code: str = "test_brand",
    brand_name: str = "测试品牌",
    sales_unit_code: str = "bag",
    sales_unit_name: str = "袋",
    barcode: str | None = "6900000000000",
    spec_text: str | None = "1kg/袋",
    price_list_code: str = "default",
    price_cents: int = 1899,
    compare_at_price_cents: int | None = 2299,
    currency: str = "USD",
    is_sellable: bool = True,
    price_is_active: bool = True,
    source_product_id: int | None = 501,
    source_sku_id: int | None = 601,
    source_price_id: int | None = 701,
) -> dict[str, str | int | None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    publish_version = _publish_version()
    now = datetime.now(UTC)
    resolved_sku_name = sku_name or display_name

    with session_factory() as session:
        session.add(
            PublishedProduct(
                publish_version=publish_version,
                pms_item_id=pms_item_id,
                pms_sku=pms_sku,
                product_code=product_code,
                product_name=display_name,
                display_name=display_name,
                description=f"{display_name} published test item",
                image_url=None,
                category_code=category_code,
                category_name=category_name,
                brand_code=brand_code,
                brand_name=brand_name,
                display_status="visible",
                sell_status="sellable",
                sort_order=10,
                visible_from=None,
                visible_until=None,
                published_at=now,
                source_product_id=source_product_id,
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
                sku_name=resolved_sku_name,
                display_sku_name=resolved_sku_name,
                sales_unit_code=sales_unit_code,
                sales_unit_name=sales_unit_name,
                barcode=barcode,
                spec_text=spec_text,
                is_sellable=is_sellable,
                sort_order=10,
                published_at=now,
                source_sku_id=source_sku_id,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
            )
        )
        session.flush()

        session.add(
            PublishedPrice(
                publish_version=publish_version,
                price_list_code=price_list_code,
                channel="storefront",
                sku_code=sku_code,
                currency=currency,
                price_cents=price_cents,
                compare_at_price_cents=compare_at_price_cents,
                effective_from=None,
                effective_until=None,
                is_active=price_is_active,
                priority=10,
                published_at=now,
                source_price_id=source_price_id,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
            )
        )
        session.commit()

    return {
        "publish_version": publish_version,
        "product_code": product_code,
        "sku_code": sku_code,
        "display_name": display_name,
        "sku_name": resolved_sku_name,
        "pms_item_id": pms_item_id,
        "pms_sku": pms_sku,
        "category_code": category_code,
        "category_name": category_name,
        "brand_code": brand_code,
        "brand_name": brand_name,
        "sales_unit_code": sales_unit_code,
        "sales_unit_name": sales_unit_name,
        "barcode": barcode,
        "spec_text": spec_text,
        "price_list_code": price_list_code,
        "price_cents": price_cents,
        "compare_at_price_cents": compare_at_price_cents,
        "source_product_id": source_product_id,
        "source_sku_id": source_sku_id,
        "source_price_id": source_price_id,
    }


def seed_default_published_catalog() -> None:
    seed_published_catalog_item(
        product_code="pet-cat-food-salmon-001",
        sku_code="CAT-FOOD-SALMON-1KG",
        display_name="三文鱼成猫粮 1kg",
        price_cents=1899,
    )
    seed_published_catalog_item(
        product_code="pet-cat-litter-tofu-001",
        sku_code="CAT-LITTER-TOFU-6L",
        display_name="豆腐猫砂 6L",
        pms_item_id=1002,
        pms_sku="PMS-CAT-LITTER-TOFU",
        category_code="cat_litter",
        category_name="猫砂",
        sales_unit_code="box",
        sales_unit_name="箱",
        barcode="6900000000001",
        spec_text="6L/箱",
        price_cents=1099,
        compare_at_price_cents=1399,
        source_product_id=502,
        source_sku_id=602,
        source_price_id=702,
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
            PublishedPromotion(
                publish_version=resolved_publish_version,
                promotion_code=promotion_code,
                promotion_name=promotion_name,
                promotion_type=promotion_type,
                discount_type=discount_type,
                discount_value=discount_value,
                scope_type=scope_type,
                min_order_amount_cents=min_order_amount_cents,
                max_discount_cents=max_discount_cents,
                currency=currency,
                starts_at=None,
                ends_at=None,
                priority=10,
                stackable=False,
                is_active=is_active,
                published_at=now,
                source_promotion_id=None,
                source_updated_at=now,
                raw_payload={"source": "pytest"},
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
