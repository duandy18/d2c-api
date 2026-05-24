"""Sync backoffice published exports into d2c-api runtime published tables."""

from __future__ import annotations

import argparse
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedPrice,
    PublishedProduct,
    PublishedPromotion,
    PublishedSku,
    PublishSyncRun,
)

VALID_SCOPES = {"catalog", "prices", "promotions", "coupons", "all"}

ENDPOINT_BY_SCOPE = {
    "catalog": "/backoffice/read/v1/published/catalog",
    "prices": "/backoffice/read/v1/published/prices",
    "promotions": "/backoffice/read/v1/published/promotions",
    "coupons": "/backoffice/read/v1/published/coupons",
}

PRODUCT_FIELDS = (
    "publish_version",
    "pms_item_id",
    "pms_sku",
    "product_code",
    "product_name",
    "display_name",
    "description",
    "image_url",
    "category_code",
    "category_name",
    "brand_code",
    "brand_name",
    "display_status",
    "sell_status",
    "sort_order",
    "visible_from",
    "visible_until",
    "published_at",
    "source_product_id",
    "source_updated_at",
    "raw_payload",
)

SKU_FIELDS = (
    "publish_version",
    "product_code",
    "sku_code",
    "sku_name",
    "display_sku_name",
    "sales_unit_code",
    "sales_unit_name",
    "barcode",
    "spec_text",
    "is_sellable",
    "sort_order",
    "published_at",
    "source_sku_id",
    "source_updated_at",
    "raw_payload",
)

PRICE_FIELDS = (
    "publish_version",
    "price_list_code",
    "channel",
    "sku_code",
    "currency",
    "price_cents",
    "compare_at_price_cents",
    "effective_from",
    "effective_until",
    "is_active",
    "priority",
    "published_at",
    "source_price_id",
    "source_updated_at",
    "raw_payload",
)

PROMOTION_FIELDS = (
    "publish_version",
    "promotion_code",
    "promotion_name",
    "promotion_type",
    "discount_type",
    "discount_value",
    "scope_type",
    "min_order_amount_cents",
    "max_discount_cents",
    "currency",
    "starts_at",
    "ends_at",
    "priority",
    "stackable",
    "is_active",
    "published_at",
    "source_promotion_id",
    "source_updated_at",
    "raw_payload",
)

COUPON_FIELDS = (
    "publish_version",
    "coupon_code",
    "coupon_name",
    "promotion_code",
    "coupon_type",
    "total_limit",
    "per_customer_limit",
    "starts_at",
    "ends_at",
    "is_active",
    "published_at",
    "source_coupon_id",
    "source_updated_at",
    "raw_payload",
)

DATETIME_FIELDS = {
    "visible_from",
    "visible_until",
    "published_at",
    "source_updated_at",
    "effective_from",
    "effective_until",
    "starts_at",
    "ends_at",
}


@dataclass(frozen=True)
class ScopeResult:
    publish_version: str | None
    rows_fetched: int
    rows_upserted: int
    rows_deleted: int = 0


JsonFetcher = Callable[[str, str, str, str | None], dict[str, Any]]


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _env_value(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    raise TypeError(f"unsupported datetime value: {value!r}")


def _normalize_row(item: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    row: dict[str, Any] = {}

    for field in fields:
        value = item.get(field)
        if field in DATETIME_FIELDS:
            value = _parse_datetime(value)
        row[field] = value

    return row


def fetch_published_export(
    base_url: str,
    endpoint: str,
    service_client: str,
    publish_version: str | None,
) -> dict[str, Any]:
    params: dict[str, str] = {}
    if publish_version is not None:
        params["publish_version"] = publish_version

    url = f"{_normalize_base_url(base_url)}{endpoint}"

    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            url,
            params=params,
            headers={"X-Service-Client": service_client},
        )
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise TypeError("published export response must be a JSON object")

    return payload


def _upsert_rows(
    session: Session,
    model: type[Any],
    rows: list[dict[str, Any]],
    conflict_columns: tuple[str, ...],
) -> int:
    if not rows:
        return 0

    statement = insert(model).values(rows)
    excluded = statement.excluded
    table_columns = model.__table__.columns

    update_values = {
        column.name: getattr(excluded, column.name)
        for column in table_columns
        if column.name in rows[0] and column.name not in {"id", "created_at"}
    }

    if "updated_at" in table_columns:
        update_values["updated_at"] = func.now()

    session.execute(
        statement.on_conflict_do_update(
            index_elements=list(conflict_columns),
            set_=update_values,
        )
    )

    # SQLAlchemy/psycopg may report rowcount as -1 for INSERT .. ON CONFLICT.
    # The sync summary records accepted export rows, not driver rowcount.
    return len(rows)


def _sync_catalog(
    session: Session,
    base_url: str,
    service_client: str,
    publish_version: str | None,
    fetcher: JsonFetcher,
) -> ScopeResult:
    payload = fetcher(base_url, ENDPOINT_BY_SCOPE["catalog"], service_client, publish_version)
    resolved_version = payload.get("publish_version") or publish_version

    products = [
        _normalize_row(item, PRODUCT_FIELDS)
        for item in payload.get("products", [])
        if isinstance(item, dict)
    ]
    skus = [
        _normalize_row(item, SKU_FIELDS)
        for item in payload.get("skus", [])
        if isinstance(item, dict)
    ]

    upserted_products = _upsert_rows(
        session,
        PublishedProduct,
        products,
        ("publish_version", "product_code"),
    )
    upserted_skus = _upsert_rows(
        session,
        PublishedSku,
        skus,
        ("publish_version", "sku_code"),
    )

    return ScopeResult(
        publish_version=resolved_version,
        rows_fetched=len(products) + len(skus),
        rows_upserted=upserted_products + upserted_skus,
    )


def _sync_prices(
    session: Session,
    base_url: str,
    service_client: str,
    publish_version: str | None,
    fetcher: JsonFetcher,
) -> ScopeResult:
    payload = fetcher(base_url, ENDPOINT_BY_SCOPE["prices"], service_client, publish_version)
    resolved_version = payload.get("publish_version") or publish_version

    prices = [
        _normalize_row(item, PRICE_FIELDS)
        for item in payload.get("prices", [])
        if isinstance(item, dict)
    ]

    rows_upserted = _upsert_rows(
        session,
        PublishedPrice,
        prices,
        ("publish_version", "price_list_code", "channel", "sku_code"),
    )

    return ScopeResult(
        publish_version=resolved_version,
        rows_fetched=len(prices),
        rows_upserted=rows_upserted,
    )


def _sync_promotions(
    session: Session,
    base_url: str,
    service_client: str,
    publish_version: str | None,
    fetcher: JsonFetcher,
) -> ScopeResult:
    payload = fetcher(base_url, ENDPOINT_BY_SCOPE["promotions"], service_client, publish_version)
    resolved_version = payload.get("publish_version") or publish_version

    promotions = [
        _normalize_row(item, PROMOTION_FIELDS)
        for item in payload.get("promotions", [])
        if isinstance(item, dict)
    ]

    rows_upserted = _upsert_rows(
        session,
        PublishedPromotion,
        promotions,
        ("publish_version", "promotion_code"),
    )

    return ScopeResult(
        publish_version=resolved_version,
        rows_fetched=len(promotions),
        rows_upserted=rows_upserted,
    )


def _sync_coupons(
    session: Session,
    base_url: str,
    service_client: str,
    publish_version: str | None,
    fetcher: JsonFetcher,
) -> ScopeResult:
    payload = fetcher(base_url, ENDPOINT_BY_SCOPE["coupons"], service_client, publish_version)
    resolved_version = payload.get("publish_version") or publish_version

    coupons = [
        _normalize_row(item, COUPON_FIELDS)
        for item in payload.get("coupons", [])
        if isinstance(item, dict)
    ]

    rows_upserted = _upsert_rows(
        session,
        PublishedCoupon,
        coupons,
        ("publish_version", "coupon_code"),
    )

    return ScopeResult(
        publish_version=resolved_version,
        rows_fetched=len(coupons),
        rows_upserted=rows_upserted,
    )


def _sync_single_scope(
    session: Session,
    scope: str,
    base_url: str,
    service_client: str,
    publish_version: str | None,
    fetcher: JsonFetcher,
) -> ScopeResult:
    if scope == "catalog":
        return _sync_catalog(session, base_url, service_client, publish_version, fetcher)
    if scope == "prices":
        return _sync_prices(session, base_url, service_client, publish_version, fetcher)
    if scope == "promotions":
        return _sync_promotions(session, base_url, service_client, publish_version, fetcher)
    if scope == "coupons":
        return _sync_coupons(session, base_url, service_client, publish_version, fetcher)

    raise ValueError(f"unsupported published sync scope: {scope}")


def _combine_results(scope: str, results: list[ScopeResult]) -> ScopeResult:
    publish_version = next(
        (result.publish_version for result in results if result.publish_version), None
    )
    return ScopeResult(
        publish_version=publish_version,
        rows_fetched=sum(result.rows_fetched for result in results),
        rows_upserted=sum(result.rows_upserted for result in results),
        rows_deleted=sum(result.rows_deleted for result in results),
    )


def sync_published_scope(
    session: Session,
    *,
    scope: str,
    base_url: str,
    service_client: str,
    publish_version: str | None,
    requested_by: str | None,
    fetcher: JsonFetcher = fetch_published_export,
) -> PublishSyncRun:
    if scope not in VALID_SCOPES:
        raise ValueError(f"unsupported published sync scope: {scope}")

    source_endpoint = "multiple" if scope == "all" else ENDPOINT_BY_SCOPE[scope]
    sync_run = PublishSyncRun(
        sync_scope=scope,
        source_service="d2c-backoffice-api",
        source_base_url=_normalize_base_url(base_url),
        source_endpoint=source_endpoint,
        publish_version=publish_version,
        status="started",
        requested_by=requested_by,
        rows_fetched=0,
        rows_upserted=0,
        rows_deleted=0,
    )
    session.add(sync_run)
    session.commit()
    sync_run_id = sync_run.id

    try:
        if scope == "all":
            results = [
                _sync_single_scope(
                    session,
                    child_scope,
                    base_url,
                    service_client,
                    publish_version,
                    fetcher,
                )
                for child_scope in ("catalog", "prices", "promotions", "coupons")
            ]
            result = _combine_results(scope, results)
        else:
            result = _sync_single_scope(
                session,
                scope,
                base_url,
                service_client,
                publish_version,
                fetcher,
            )

        sync_run.publish_version = result.publish_version
        sync_run.status = "success"
        sync_run.finished_at = datetime.now(UTC)
        sync_run.rows_fetched = result.rows_fetched
        sync_run.rows_upserted = result.rows_upserted
        sync_run.rows_deleted = result.rows_deleted
        sync_run.raw_summary = {
            "scope": scope,
            "publish_version": result.publish_version,
            "rows_fetched": result.rows_fetched,
            "rows_upserted": result.rows_upserted,
            "rows_deleted": result.rows_deleted,
        }
        session.commit()
    except Exception as exc:
        session.rollback()
        failed_sync_run = session.get(PublishSyncRun, sync_run_id)

        if failed_sync_run is not None:
            failed_sync_run.status = "failed"
            failed_sync_run.finished_at = datetime.now(UTC)
            failed_sync_run.error_code = type(exc).__name__
            failed_sync_run.error_message = str(exc)
            failed_sync_run.raw_summary = {
                "scope": scope,
                "publish_version": publish_version,
                "error": str(exc),
            }
            session.commit()

        raise

    return sync_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync D2C published runtime tables.")
    parser.add_argument(
        "--scope",
        choices=sorted(VALID_SCOPES),
        required=True,
        help="Published sync scope.",
    )
    parser.add_argument(
        "--source-base-url",
        default=_env_value("D2C_BACKOFFICE_API_BASE_URL", "http://127.0.0.1:8026"),
        help="D2C backoffice API base URL.",
    )
    parser.add_argument(
        "--service-client",
        default=_env_value("D2C_SERVICE_CLIENT_CODE", load_settings().service_client_code),
        help="Service client header value for backoffice read-v1 export.",
    )
    parser.add_argument(
        "--publish-version",
        default=_env_optional("D2C_PUBLISH_VERSION"),
        help="Optional publish version to sync.",
    )
    parser.add_argument(
        "--requested-by",
        default=_env_value("D2C_PUBLISH_SYNC_REQUESTED_BY", "cli"),
        help="Actor recorded in d2c_publish_sync_runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)

    with session_factory() as session:
        sync_run = sync_published_scope(
            session,
            scope=args.scope,
            base_url=args.source_base_url,
            service_client=args.service_client,
            publish_version=args.publish_version,
            requested_by=args.requested_by,
        )
        summary = {
            "id": sync_run.id,
            "scope": sync_run.sync_scope,
            "status": sync_run.status,
            "publish_version": sync_run.publish_version,
            "rows_fetched": sync_run.rows_fetched,
            "rows_upserted": sync_run.rows_upserted,
            "rows_deleted": sync_run.rows_deleted,
        }

    print(summary)


if __name__ == "__main__":
    main()
