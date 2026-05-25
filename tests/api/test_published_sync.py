from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.config import load_settings
from app.core.database import get_session_factory
from app.domains.published.models.published import (
    PublishedCoupon,
    PublishSyncRun,
)
from scripts.published.sync_published import sync_published_scope


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def _export_payloads(publish_version: str) -> dict[str, dict[str, object]]:
    coupon_code = _code("COUPON")
    now = datetime.now(UTC).isoformat()

    return {
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

        coupon = session.scalar(
            select(PublishedCoupon).where(PublishedCoupon.publish_version == publish_version)
        )

        assert sync_run.status == "success"
        assert sync_run.rows_fetched == 1
        assert sync_run.rows_upserted == 1
        assert sync_run.rows_deleted == 0
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
                scope="coupons",
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


def test_legacy_catalog_sync_scopes_are_retired() -> None:
    settings = load_settings()
    session_factory = get_session_factory(settings.test_database_url)

    with session_factory() as session:
        for scope in ("catalog", "prices"):
            with pytest.raises(ValueError, match="unsupported published sync scope"):
                sync_published_scope(
                    session,
                    scope=scope,
                    base_url="http://backoffice.test",
                    service_client="d2c-service",
                    publish_version=_code("PUB"),
                    requested_by="pytest",
                    fetcher=lambda *_args: {},
                )
