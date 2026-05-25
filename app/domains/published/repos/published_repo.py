"""Runtime published model repositories."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedCoupon,
    PublishSyncRun,
)


def list_published_coupons(session: Session) -> list[PublishedCoupon]:
    statement = select(PublishedCoupon).order_by(
        PublishedCoupon.publish_version,
        PublishedCoupon.id,
    )
    return list(session.scalars(statement).all())


def list_publish_sync_runs(session: Session) -> list[PublishSyncRun]:
    statement = select(PublishSyncRun).order_by(PublishSyncRun.id.desc())
    return list(session.scalars(statement).all())
