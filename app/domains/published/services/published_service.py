"""Runtime published model services."""

from sqlalchemy.orm import Session

from app.domains.published.contracts.published_contract import (
    PublishedCouponContract,
    PublishedCouponsResponse,
    PublishedHealthResponse,
    PublishedPriceContract,
    PublishedPricesResponse,
    PublishedProductContract,
    PublishedProductsResponse,
    PublishedPromotionContract,
    PublishedPromotionsResponse,
    PublishedSkuContract,
    PublishedSkusResponse,
    PublishSyncRunContract,
    PublishSyncRunsResponse,
)
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedPrice,
    PublishedProduct,
    PublishedPromotion,
    PublishedSku,
    PublishSyncRun,
)
from app.domains.published.repos.published_repo import (
    list_publish_sync_runs,
    list_published_coupons,
    list_published_prices,
    list_published_products,
    list_published_promotions,
    list_published_skus,
)


def get_published_health() -> PublishedHealthResponse:
    return PublishedHealthResponse(
        status="ok",
        module="published",
        storage="d2c_published_runtime_model",
    )


def _build_product(row: PublishedProduct) -> PublishedProductContract:
    return PublishedProductContract(
        id=row.id,
        publish_version=row.publish_version,
        pms_item_id=row.pms_item_id,
        pms_sku=row.pms_sku,
        product_code=row.product_code,
        product_name=row.product_name,
        display_name=row.display_name,
        description=row.description,
        image_url=row.image_url,
        category_code=row.category_code,
        category_name=row.category_name,
        brand_code=row.brand_code,
        brand_name=row.brand_name,
        display_status=row.display_status,
        sell_status=row.sell_status,
        sort_order=row.sort_order,
        visible_from=row.visible_from,
        visible_until=row.visible_until,
        published_at=row.published_at,
        source_product_id=row.source_product_id,
        source_updated_at=row.source_updated_at,
        raw_payload=row.raw_payload,
    )


def get_published_products(session: Session) -> PublishedProductsResponse:
    rows = [_build_product(row) for row in list_published_products(session)]
    return PublishedProductsResponse(count=len(rows), products=rows)


def _build_sku(row: PublishedSku) -> PublishedSkuContract:
    return PublishedSkuContract(
        id=row.id,
        publish_version=row.publish_version,
        product_code=row.product_code,
        sku_code=row.sku_code,
        sku_name=row.sku_name,
        display_sku_name=row.display_sku_name,
        sales_unit_code=row.sales_unit_code,
        sales_unit_name=row.sales_unit_name,
        barcode=row.barcode,
        spec_text=row.spec_text,
        is_sellable=row.is_sellable,
        sort_order=row.sort_order,
        published_at=row.published_at,
        source_sku_id=row.source_sku_id,
        source_updated_at=row.source_updated_at,
        raw_payload=row.raw_payload,
    )


def get_published_skus(session: Session) -> PublishedSkusResponse:
    rows = [_build_sku(row) for row in list_published_skus(session)]
    return PublishedSkusResponse(count=len(rows), skus=rows)


def _build_price(row: PublishedPrice) -> PublishedPriceContract:
    return PublishedPriceContract(
        id=row.id,
        publish_version=row.publish_version,
        price_list_code=row.price_list_code,
        channel=row.channel,
        sku_code=row.sku_code,
        currency=row.currency,
        price_cents=row.price_cents,
        compare_at_price_cents=row.compare_at_price_cents,
        effective_from=row.effective_from,
        effective_until=row.effective_until,
        is_active=row.is_active,
        priority=row.priority,
        published_at=row.published_at,
        source_price_id=row.source_price_id,
        source_updated_at=row.source_updated_at,
        raw_payload=row.raw_payload,
    )


def get_published_prices(session: Session) -> PublishedPricesResponse:
    rows = [_build_price(row) for row in list_published_prices(session)]
    return PublishedPricesResponse(count=len(rows), prices=rows)


def _build_promotion(row: PublishedPromotion) -> PublishedPromotionContract:
    return PublishedPromotionContract(
        id=row.id,
        publish_version=row.publish_version,
        promotion_code=row.promotion_code,
        promotion_name=row.promotion_name,
        promotion_type=row.promotion_type,
        discount_type=row.discount_type,
        discount_value=row.discount_value,
        scope_type=row.scope_type,
        min_order_amount_cents=row.min_order_amount_cents,
        max_discount_cents=row.max_discount_cents,
        currency=row.currency,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        priority=row.priority,
        stackable=row.stackable,
        is_active=row.is_active,
        published_at=row.published_at,
        source_promotion_id=row.source_promotion_id,
        source_updated_at=row.source_updated_at,
        raw_payload=row.raw_payload,
    )


def get_published_promotions(session: Session) -> PublishedPromotionsResponse:
    rows = [_build_promotion(row) for row in list_published_promotions(session)]
    return PublishedPromotionsResponse(count=len(rows), promotions=rows)


def _build_coupon(row: PublishedCoupon) -> PublishedCouponContract:
    return PublishedCouponContract(
        id=row.id,
        publish_version=row.publish_version,
        coupon_code=row.coupon_code,
        coupon_name=row.coupon_name,
        promotion_code=row.promotion_code,
        coupon_type=row.coupon_type,
        total_limit=row.total_limit,
        per_customer_limit=row.per_customer_limit,
        starts_at=row.starts_at,
        ends_at=row.ends_at,
        is_active=row.is_active,
        published_at=row.published_at,
        source_coupon_id=row.source_coupon_id,
        source_updated_at=row.source_updated_at,
        raw_payload=row.raw_payload,
    )


def get_published_coupons(session: Session) -> PublishedCouponsResponse:
    rows = [_build_coupon(row) for row in list_published_coupons(session)]
    return PublishedCouponsResponse(count=len(rows), coupons=rows)


def _build_sync_run(row: PublishSyncRun) -> PublishSyncRunContract:
    return PublishSyncRunContract(
        id=row.id,
        sync_scope=row.sync_scope,
        source_service=row.source_service,
        source_base_url=row.source_base_url,
        source_endpoint=row.source_endpoint,
        publish_version=row.publish_version,
        status=row.status,
        started_at=row.started_at,
        finished_at=row.finished_at,
        requested_by=row.requested_by,
        rows_fetched=row.rows_fetched,
        rows_upserted=row.rows_upserted,
        rows_deleted=row.rows_deleted,
        error_code=row.error_code,
        error_message=row.error_message,
        raw_summary=row.raw_summary,
    )


def get_publish_sync_runs(session: Session) -> PublishSyncRunsResponse:
    rows = [_build_sync_run(row) for row in list_publish_sync_runs(session)]
    return PublishSyncRunsResponse(count=len(rows), sync_runs=rows)
