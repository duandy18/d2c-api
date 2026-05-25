"""Storefront home repositories backed by terminal published snapshots."""

from __future__ import annotations

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedClientActionPolicy,
    PublishedClientDataBinding,
    PublishedClientPage,
    PublishedClientRegion,
    PublishedClientTrackingPolicy,
    PublishedClientVisibilityRule,
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
]


def _visible_page_filters() -> tuple[object, ...]:
    return (
        PublishedClientPage.display_status == "visible",
        PublishedClientPage.is_active.is_(True),
    )


def _visible_region_filters() -> tuple[object, ...]:
    return (
        PublishedClientRegion.display_status == "visible",
        PublishedClientRegion.is_active.is_(True),
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


def latest_client_home_publish_version(
    session: Session,
    page_code: str = "home",
) -> str | None:
    statement = (
        select(PublishedClientPage.publish_version)
        .where(PublishedClientPage.page_code == page_code)
        .where(*_visible_page_filters())
        .order_by(PublishedClientPage.published_at.desc(), PublishedClientPage.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


def get_home_page(
    session: Session,
    publish_version: str,
    page_code: str = "home",
) -> PublishedClientPage | None:
    statement = (
        select(PublishedClientPage)
        .where(PublishedClientPage.publish_version == publish_version)
        .where(PublishedClientPage.page_code == page_code)
        .where(*_visible_page_filters())
        .limit(1)
    )
    return session.scalar(statement)


def list_home_regions(
    session: Session,
    publish_version: str,
    page_code: str,
) -> list[PublishedClientRegion]:
    statement = (
        select(PublishedClientRegion)
        .where(PublishedClientRegion.publish_version == publish_version)
        .where(PublishedClientRegion.page_code == page_code)
        .where(*_visible_region_filters())
        .order_by(PublishedClientRegion.sort_order, PublishedClientRegion.id)
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


def list_home_data_bindings(
    session: Session,
    publish_version: str,
) -> list[PublishedClientDataBinding]:
    statement = (
        select(PublishedClientDataBinding)
        .where(PublishedClientDataBinding.publish_version == publish_version)
        .where(PublishedClientDataBinding.is_active.is_(True))
        .order_by(PublishedClientDataBinding.binding_code, PublishedClientDataBinding.id)
    )
    return list(session.scalars(statement).all())


def list_home_visibility_rules(
    session: Session,
    publish_version: str,
) -> list[PublishedClientVisibilityRule]:
    statement = (
        select(PublishedClientVisibilityRule)
        .where(PublishedClientVisibilityRule.publish_version == publish_version)
        .where(PublishedClientVisibilityRule.is_active.is_(True))
        .order_by(PublishedClientVisibilityRule.priority, PublishedClientVisibilityRule.id)
    )
    return list(session.scalars(statement).all())


def list_home_action_policies(
    session: Session,
    publish_version: str,
) -> list[PublishedClientActionPolicy]:
    statement = (
        select(PublishedClientActionPolicy)
        .where(PublishedClientActionPolicy.publish_version == publish_version)
        .where(PublishedClientActionPolicy.is_active.is_(True))
        .order_by(PublishedClientActionPolicy.policy_code, PublishedClientActionPolicy.id)
    )
    return list(session.scalars(statement).all())


def list_home_tracking_policies(
    session: Session,
    publish_version: str,
) -> list[PublishedClientTrackingPolicy]:
    statement = (
        select(PublishedClientTrackingPolicy)
        .where(PublishedClientTrackingPolicy.publish_version == publish_version)
        .where(PublishedClientTrackingPolicy.is_active.is_(True))
        .order_by(PublishedClientTrackingPolicy.policy_code, PublishedClientTrackingPolicy.id)
    )
    return list(session.scalars(statement).all())


def _home_rows_query(publish_version: str) -> Select[StorefrontHomeRow]:
    return (
        select(
            PublishedStorefrontSection,
            PublishedStorefrontSectionPosition,
            PublishedOffer,
            PublishedOfferPrice,
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
    return [(section, position, offer, price) for section, position, offer, price in rows]
