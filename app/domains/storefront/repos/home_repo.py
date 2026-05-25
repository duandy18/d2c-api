"""Storefront home repositories backed by terminal published snapshots."""

from __future__ import annotations

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPosition,
    PublishedOfferPrice,
    PublishedStorefrontSection,
    PublishedStorefrontSectionLayout,
)

StorefrontHomeRow = tuple[
    PublishedGroup,
    PublishedOfferPosition,
    PublishedOffer,
    PublishedOfferPrice,
]


def latest_storefront_publish_version(session: Session) -> str | None:
    statement = (
        select(PublishedOffer.publish_version)
        .where(PublishedOffer.display_status == "visible")
        .where(PublishedOffer.sell_status == "sellable")
        .order_by(PublishedOffer.published_at.desc(), PublishedOffer.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def _visible_group_filters() -> tuple[object, ...]:
    return (
        PublishedGroup.display_status == "visible",
        PublishedGroup.is_active.is_(True),
    )


def _visible_section_filters() -> tuple[object, ...]:
    return (
        PublishedStorefrontSection.display_status == "visible",
        PublishedStorefrontSection.is_active.is_(True),
    )


def _visible_offer_filters() -> tuple[object, ...]:
    return (
        PublishedOffer.display_status == "visible",
        PublishedOffer.sell_status == "sellable",
    )


def _active_position_filters() -> tuple[object, ...]:
    return (
        PublishedOfferPosition.is_active.is_(True),
        or_(
            PublishedOfferPosition.visible_from.is_(None),
            PublishedOfferPosition.visible_from <= func.now(),
        ),
        or_(
            PublishedOfferPosition.visible_until.is_(None),
            PublishedOfferPosition.visible_until > func.now(),
        ),
    )


def _active_price_filters() -> tuple[object, ...]:
    return (
        PublishedOfferPrice.channel == "storefront",
        PublishedOfferPrice.is_active.is_(True),
        or_(
            PublishedOfferPrice.effective_from.is_(None),
            PublishedOfferPrice.effective_from <= func.now(),
        ),
        or_(
            PublishedOfferPrice.effective_until.is_(None),
            PublishedOfferPrice.effective_until > func.now(),
        ),
    )


def list_home_groups(
    session: Session,
    publish_version: str,
) -> list[PublishedGroup]:
    statement = (
        select(PublishedGroup)
        .where(PublishedGroup.publish_version == publish_version)
        .where(*_visible_group_filters())
        .order_by(PublishedGroup.sort_order, PublishedGroup.id)
    )
    return list(session.scalars(statement).all())


def list_home_sections(
    session: Session,
    publish_version: str,
) -> list[PublishedStorefrontSection]:
    statement = (
        select(PublishedStorefrontSection)
        .where(PublishedStorefrontSection.publish_version == publish_version)
        .where(*_visible_section_filters())
        .order_by(PublishedStorefrontSection.sort_order, PublishedStorefrontSection.id)
    )
    return list(session.scalars(statement).all())


def list_home_layouts(
    session: Session,
    publish_version: str,
) -> list[PublishedStorefrontSectionLayout]:
    statement = (
        select(PublishedStorefrontSectionLayout)
        .where(PublishedStorefrontSectionLayout.publish_version == publish_version)
        .order_by(
            PublishedStorefrontSectionLayout.section_code, PublishedStorefrontSectionLayout.id
        )
    )
    return list(session.scalars(statement).all())


def _home_rows_query(publish_version: str) -> Select[StorefrontHomeRow]:
    return (
        select(
            PublishedGroup,
            PublishedOfferPosition,
            PublishedOffer,
            PublishedOfferPrice,
        )
        .select_from(PublishedGroup)
        .join(
            PublishedOfferPosition,
            and_(
                PublishedOfferPosition.publish_version == PublishedGroup.publish_version,
                PublishedOfferPosition.group_code == PublishedGroup.group_code,
            ),
        )
        .join(
            PublishedOffer,
            and_(
                PublishedOffer.publish_version == PublishedOfferPosition.publish_version,
                PublishedOffer.offer_code == PublishedOfferPosition.offer_code,
            ),
        )
        .join(
            PublishedOfferPrice,
            and_(
                PublishedOfferPrice.publish_version == PublishedOffer.publish_version,
                PublishedOfferPrice.offer_code == PublishedOffer.offer_code,
            ),
        )
        .where(PublishedGroup.publish_version == publish_version)
        .where(PublishedOfferPosition.publish_version == publish_version)
        .where(PublishedOffer.publish_version == publish_version)
        .where(PublishedOfferPrice.publish_version == publish_version)
        .where(*_visible_group_filters())
        .where(*_visible_offer_filters())
        .where(*_active_position_filters())
        .where(*_active_price_filters())
        .order_by(
            PublishedGroup.sort_order,
            PublishedGroup.id,
            PublishedOfferPosition.sort_order,
            PublishedOfferPosition.id,
            PublishedOfferPrice.priority,
            PublishedOfferPrice.id,
        )
    )


def list_home_rows(
    session: Session,
    publish_version: str,
) -> list[StorefrontHomeRow]:
    rows = session.execute(_home_rows_query(publish_version)).all()
    return [(group, position, offer, price) for group, position, offer, price in rows]
