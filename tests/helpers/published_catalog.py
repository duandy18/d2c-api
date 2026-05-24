"""Published catalog seed helpers for storefront runtime tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import PublishedPrice, PublishedProduct, PublishedSku


def _publish_version() -> str:
    return f"TEST-PUB-{uuid4().hex[:16].upper()}"


def seed_published_catalog_item(
    *,
    product_code: str,
    sku_code: str,
    display_name: str,
    sku_name: str | None = None,
    category_code: str = "cat_food",
    category_name: str = "猫粮",
    brand_code: str = "test_brand",
    brand_name: str = "测试品牌",
    price_cents: int = 1899,
    currency: str = "USD",
    is_sellable: bool = True,
    price_is_active: bool = True,
) -> dict[str, str | int]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    publish_version = _publish_version()
    now = datetime.now(UTC)
    resolved_sku_name = sku_name or display_name

    with session_factory() as session:
        session.add(
            PublishedProduct(
                publish_version=publish_version,
                pms_item_id=None,
                pms_sku=None,
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
                source_product_id=None,
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
                sales_unit_code="bag",
                sales_unit_name="袋",
                barcode=None,
                spec_text=None,
                is_sellable=is_sellable,
                sort_order=10,
                published_at=now,
                source_sku_id=None,
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
                currency=currency,
                price_cents=price_cents,
                compare_at_price_cents=None,
                effective_from=None,
                effective_until=None,
                is_active=price_is_active,
                priority=10,
                published_at=now,
                source_price_id=None,
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
        "price_cents": price_cents,
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
        category_code="cat_litter",
        category_name="猫砂",
        price_cents=1099,
    )
