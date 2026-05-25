from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedPrice,
    PublishedProduct,
    PublishedSku,
    PublishSyncRun,
)
from scripts.published.sync_published import sync_published_scope


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def _export_payloads(publish_version: str) -> dict[str, dict[str, object]]:
    product_code = _code("PRODUCT")
    sku_code = _code("SKU")
    coupon_code = _code("COUPON")
    now = datetime.now(UTC).isoformat()

    return {
        "/backoffice/read/v1/published/catalog": {
            "publish_version": publish_version,
            "product_count": 1,
            "sku_count": 1,
            "products": [
                {
                    "publish_version": publish_version,
                    "pms_item_id": 1001,
                    "pms_sku": "PMS-1001",
                    "product_code": product_code,
                    "product_name": "PMS Product",
                    "display_name": "Runtime Product",
                    "description": "Runtime description",
                    "image_url": "https://example.test/product.png",
                    "category_code": "cat",
                    "category_name": "Category",
                    "brand_code": "brand",
                    "brand_name": "Brand",
                    "display_status": "visible",
                    "sell_status": "sellable",
                    "sort_order": 10,
                    "visible_from": None,
                    "visible_until": None,
                    "published_at": now,
                    "source_product_id": 1,
                    "source_updated_at": now,
                    "raw_payload": {"source": "pytest"},
                }
            ],
            "skus": [
                {
                    "publish_version": publish_version,
                    "product_code": product_code,
                    "sku_code": sku_code,
                    "sku_name": "PMS Product",
                    "display_sku_name": "Runtime SKU",
                    "sales_unit_code": "bag",
                    "sales_unit_name": "Bag",
                    "barcode": "6900000000000",
                    "spec_text": "1kg",
                    "is_sellable": True,
                    "sort_order": 10,
                    "published_at": now,
                    "source_sku_id": 2,
                    "source_updated_at": now,
                    "raw_payload": {"source": "pytest"},
                }
            ],
        },
        "/backoffice/read/v1/published/prices": {
            "publish_version": publish_version,
            "count": 1,
            "prices": [
                {
                    "publish_version": publish_version,
                    "price_list_code": "default",
                    "channel": "storefront",
                    "sku_code": sku_code,
                    "currency": "USD",
                    "price_cents": 1234,
                    "compare_at_price_cents": 1500,
                    "effective_from": None,
                    "effective_until": None,
                    "is_active": True,
                    "priority": 10,
                    "published_at": now,
                    "source_price_id": 3,
                    "source_updated_at": now,
                    "raw_payload": {"source": "pytest"},
                }
            ],
        },
        "/backoffice/read/v1/published/coupons": {
            "publish_version": publish_version,
            "count": 1,
            "coupons": [
                {
                    "publish_version": publish_version,
                    "coupon_code": coupon_code,
                    "coupon_name": "Runtime Coupon",
                    "promotion_code": _code("PROMO"),
                    "coupon_type": "public_code",
                    "total_limit": 100,
                    "per_customer_limit": 1,
                    "starts_at": None,
                    "ends_at": None,
                    "is_active": True,
                    "published_at": now,
                    "source_coupon_id": 5,
                    "source_updated_at": now,
                    "raw_payload": {"source": "pytest"},
                }
            ],
        },
    }


def test_sync_published_all_upserts_runtime_tables() -> None:
    publish_version = _code("PUB")
    payloads = _export_payloads(publish_version)

    def fake_fetcher(
        _base_url: str,
        endpoint: str,
        _service_client: str,
        requested_publish_version: str | None,
    ) -> dict[str, object]:
        assert requested_publish_version == publish_version
        return payloads[endpoint]

    settings = load_settings()
    session_factory = get_session_factory(settings.test_database_url)

    with session_factory() as session:
        sync_run = sync_published_scope(
            session,
            scope="all",
            base_url="http://backoffice.test",
            service_client="d2c-service",
            publish_version=publish_version,
            requested_by="pytest",
            fetcher=fake_fetcher,
        )

        product_count = len(
            session.scalars(
                select(PublishedProduct).where(PublishedProduct.publish_version == publish_version)
            ).all()
        )
        sku_count = len(
            session.scalars(
                select(PublishedSku).where(PublishedSku.publish_version == publish_version)
            ).all()
        )
        price = session.scalar(
            select(PublishedPrice).where(PublishedPrice.publish_version == publish_version)
        )
        coupon = session.scalar(
            select(PublishedCoupon).where(PublishedCoupon.publish_version == publish_version)
        )

        assert sync_run.status == "success"
        assert sync_run.rows_fetched == 4
        assert sync_run.rows_upserted == 4
        assert sync_run.rows_deleted == 0
        assert product_count == 1
        assert sku_count == 1
        assert price is not None
        assert price.price_cents == 1234
        assert coupon is not None
        assert coupon.per_customer_limit == 1


def test_sync_published_failure_is_recorded() -> None:
    publish_version = _code("PUB")

    def failing_fetcher(
        _base_url: str,
        _endpoint: str,
        _service_client: str,
        _publish_version: str | None,
    ) -> dict[str, object]:
        raise RuntimeError("backoffice_export_failed")

    settings = load_settings()
    session_factory = get_session_factory(settings.test_database_url)

    with session_factory() as session:
        with pytest.raises(RuntimeError, match="backoffice_export_failed"):
            sync_published_scope(
                session,
                scope="catalog",
                base_url="http://backoffice.test",
                service_client="d2c-service",
                publish_version=publish_version,
                requested_by="pytest",
                fetcher=failing_fetcher,
            )

        sync_run = session.scalar(
            select(PublishSyncRun)
            .where(PublishSyncRun.publish_version == publish_version)
            .order_by(PublishSyncRun.id.desc())
        )

        assert sync_run is not None
        assert sync_run.status == "failed"
        assert sync_run.error_code == "RuntimeError"
        assert sync_run.error_message == "backoffice_export_failed"
