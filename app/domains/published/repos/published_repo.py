"""Runtime published model repositories."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedCoupon,
    PublishedPrice,
    PublishedProduct,
    PublishedSku,
    PublishSyncRun,
)


def list_published_products(session: Session) -> list[PublishedProduct]:
    statement = select(PublishedProduct).order_by(
        PublishedProduct.publish_version,
        PublishedProduct.sort_order,
        PublishedProduct.id,
    )
    return list(session.scalars(statement).all())


def list_published_skus(session: Session) -> list[PublishedSku]:
    statement = select(PublishedSku).order_by(
        PublishedSku.publish_version,
        PublishedSku.product_code,
        PublishedSku.sort_order,
        PublishedSku.id,
    )
    return list(session.scalars(statement).all())


def list_published_prices(session: Session) -> list[PublishedPrice]:
    statement = select(PublishedPrice).order_by(
        PublishedPrice.publish_version,
        PublishedPrice.priority,
        PublishedPrice.id,
    )
    return list(session.scalars(statement).all())


def list_published_coupons(session: Session) -> list[PublishedCoupon]:
    statement = select(PublishedCoupon).order_by(
        PublishedCoupon.publish_version,
        PublishedCoupon.id,
    )
    return list(session.scalars(statement).all())


def list_publish_sync_runs(session: Session) -> list[PublishSyncRun]:
    statement = select(PublishSyncRun).order_by(PublishSyncRun.id.desc())
    return list(session.scalars(statement).all())
