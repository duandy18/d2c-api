"""Storefront home repositories backed by terminal published snapshots."""

from __future__ import annotations

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPrice,
    PublishedStorefrontSection,
    PublishedStorefrontSectionLayout,
    PublishedStorefrontSectionPosition,
)

StorefrontHomeRow = tuple[
    PublishedStorefrontSection,
    PublishedStorefrontSectionPosition,
    PublishedOffer,
    PublishedOfferPrice,
    PublishedGroup | None,
]


def latest_storefront_publish_version(session: Session) -> str | None:
    statement = (
        select(PublishedStorefrontSectionPosition.publish_version)
        .order_by(
            PublishedStorefrontSectionPosition.published_at.desc(),
            PublishedStorefrontSectionPosition.id.desc(),
        )
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


def _active_section_position_filters() -> tuple[object, ...]:
    return (
        PublishedStorefrontSectionPosition.is_active.is_(True),
        or_(
            PublishedStorefrontSectionPosition.visible_from.is_(None),
            PublishedStorefrontSectionPosition.visible_from <= func.now(),
        ),
        or_(
            PublishedStorefrontSectionPosition.visible_until.is_(None),
            PublishedStorefrontSectionPosition.visible_until > func.now(),
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
            PublishedStorefrontSectionLayout.section_code,
            PublishedStorefrontSectionLayout.id,
        )
    )
    return list(session.scalars(statement).all())


def _home_rows_query(publish_version: str) -> Select[StorefrontHomeRow]:
    return (
        select(
            PublishedStorefrontSection,
            PublishedStorefrontSectionPosition,
            PublishedOffer,
            PublishedOfferPrice,
            PublishedGroup,
        )
        .select_from(PublishedStorefrontSection)
        .join(
            PublishedStorefrontSectionPosition,
            and_(
                PublishedStorefrontSectionPosition.publish_version
                == PublishedStorefrontSection.publish_version,
                PublishedStorefrontSectionPosition.section_code
                == PublishedStorefrontSection.section_code,
            ),
        )
        .join(
            PublishedOffer,
            and_(
                PublishedOffer.publish_version
                == PublishedStorefrontSectionPosition.publish_version,
                PublishedOffer.offer_code == PublishedStorefrontSectionPosition.offer_code,
            ),
        )
        .join(
            PublishedOfferPrice,
            and_(
                PublishedOfferPrice.publish_version == PublishedOffer.publish_version,
                PublishedOfferPrice.offer_code == PublishedOffer.offer_code,
            ),
        )
        .outerjoin(
            PublishedGroup,
            and_(
                PublishedGroup.publish_version == PublishedStorefrontSection.publish_version,
                PublishedGroup.group_code == PublishedStorefrontSection.group_code,
                *_visible_group_filters(),
            ),
        )
        .where(PublishedStorefrontSection.publish_version == publish_version)
        .where(PublishedStorefrontSectionPosition.publish_version == publish_version)
        .where(PublishedOffer.publish_version == publish_version)
        .where(PublishedOfferPrice.publish_version == publish_version)
        .where(*_visible_section_filters())
        .where(*_active_section_position_filters())
        .where(*_visible_offer_filters())
        .where(*_active_price_filters())
        .order_by(
            PublishedStorefrontSection.sort_order,
            PublishedStorefrontSection.id,
            PublishedStorefrontSectionPosition.sort_order,
            PublishedStorefrontSectionPosition.id,
            PublishedOfferPrice.priority,
            PublishedOfferPrice.id,
        )
    )


def list_home_rows(
    session: Session,
    publish_version: str,
) -> list[StorefrontHomeRow]:
    rows = session.execute(_home_rows_query(publish_version)).all()
    return [
        (section, position, offer, price, group)
        for section, position, offer, price, group in rows
    ]
