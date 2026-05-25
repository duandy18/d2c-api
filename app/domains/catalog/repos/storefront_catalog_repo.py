"""Storefront catalog repositories.

The public storefront catalog now reads terminal published Offer snapshots.
Older runtime catalog tables stay available for cart/order until those flows
are cut in later steps, but catalog no longer reads them.
"""

from __future__ import annotations

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPosition,
    PublishedOfferPrice,
)

PublishedCatalogRow = tuple[PublishedOffer, PublishedOfferPrice, PublishedGroup | None]
PublishedCategoryRow = tuple[str, str, int]


def _latest_offer_publish_version(session: Session) -> str | None:
    statement = (
        select(PublishedOffer.publish_version)
        .where(PublishedOffer.display_status == "visible")
        .where(PublishedOffer.sell_status == "sellable")
        .order_by(PublishedOffer.published_at.desc(), PublishedOffer.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def _published_offer_filters() -> tuple[object, ...]:
    return (
        PublishedOffer.display_status == "visible",
        PublishedOffer.sell_status == "sellable",
    )


def _published_group_filters() -> tuple[object, ...]:
    return (
        PublishedGroup.display_status == "visible",
        PublishedGroup.is_active.is_(True),
    )


def _published_position_filters() -> tuple[object, ...]:
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


def _published_price_filters() -> tuple[object, ...]:
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


def _base_catalog_query(
    publish_version: str,
) -> Select[tuple[PublishedOffer, PublishedOfferPrice, PublishedGroup | None]]:
    return (
        select(PublishedOffer, PublishedOfferPrice, PublishedGroup)
        .join(
            PublishedOfferPrice,
            (PublishedOfferPrice.publish_version == PublishedOffer.publish_version)
            & (PublishedOfferPrice.offer_code == PublishedOffer.offer_code),
        )
        .outerjoin(
            PublishedOfferPosition,
            (PublishedOfferPosition.publish_version == PublishedOffer.publish_version)
            & (PublishedOfferPosition.offer_code == PublishedOffer.offer_code),
        )
        .outerjoin(
            PublishedGroup,
            (PublishedGroup.publish_version == PublishedOfferPosition.publish_version)
            & (PublishedGroup.group_code == PublishedOfferPosition.group_code),
        )
        .where(PublishedOffer.publish_version == publish_version)
        .where(PublishedOfferPrice.publish_version == publish_version)
        .where(*_published_offer_filters())
        .where(*_published_price_filters())
        .where(
            or_(
                PublishedOfferPosition.id.is_(None),
                *_published_position_filters(),
            )
        )
        .where(
            or_(
                PublishedGroup.id.is_(None),
                *_published_group_filters(),
            )
        )
        .order_by(
            PublishedGroup.sort_order.nullslast(),
            PublishedOfferPosition.sort_order.nullslast(),
            PublishedOffer.id,
            PublishedOfferPrice.priority,
            PublishedOfferPrice.id,
        )
    )


def list_active_categories(session: Session) -> list[PublishedCategoryRow]:
    publish_version = _latest_offer_publish_version(session)

    if publish_version is None:
        return []

    statement = (
        select(
            PublishedGroup.group_code,
            PublishedGroup.group_name,
            PublishedGroup.sort_order,
        )
        .where(PublishedGroup.publish_version == publish_version)
        .where(*_published_group_filters())
        .order_by(PublishedGroup.sort_order, PublishedGroup.id)
    )

    rows = session.execute(statement).all()
    return [
        (
            str(group_code),
            str(group_name),
            int(sort_order or 0),
        )
        for group_code, group_name, sort_order in rows
    ]


def list_active_catalog_rows(session: Session) -> list[PublishedCatalogRow]:
    publish_version = _latest_offer_publish_version(session)

    if publish_version is None:
        return []

    rows = session.execute(_base_catalog_query(publish_version)).all()
    return [(offer, price, group) for offer, price, group in rows]


def get_active_catalog_row_by_offer_code(
    session: Session,
    offer_code: str,
) -> PublishedCatalogRow | None:
    publish_version = _latest_offer_publish_version(session)

    if publish_version is None:
        return None

    statement = _base_catalog_query(publish_version).where(PublishedOffer.offer_code == offer_code)
    row = session.execute(statement).first()

    if row is None:
        return None

    offer, price, group = row
    return offer, price, group
