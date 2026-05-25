"""Runtime published model services."""

from sqlalchemy.orm import Session

from app.domains.published.contracts.published_contract import (
    PublishedCouponContract,
    PublishedCouponsResponse,
    PublishedHealthResponse,
    PublishSyncRunContract,
    PublishSyncRunsResponse,
)
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishSyncRun,
)
from app.domains.published.repos.published_repo import (
    list_publish_sync_runs,
    list_published_coupons,
)


def get_published_health() -> PublishedHealthResponse:
    return PublishedHealthResponse(
        status="ok",
        module="published",
        storage="d2c_published_runtime_model",
    )


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
