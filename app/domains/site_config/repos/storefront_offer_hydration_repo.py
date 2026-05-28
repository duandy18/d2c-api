"""Published Offer hydration repositories for site configuration."""

from __future__ import annotations

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.domains.published.models.published import PublishedOffer, PublishedOfferPrice

PublishedOfferPriceRow = tuple[PublishedOffer, PublishedOfferPrice]


def latest_offer_publish_version(session: Session) -> str | None:
    statement = (
        select(PublishedOffer.publish_version)
        .where(PublishedOffer.display_status == "visible")
        .where(PublishedOffer.sell_status == "sellable")
        .order_by(PublishedOffer.published_at.desc(), PublishedOffer.id.desc())
        .limit(1)
    )
    return session.scalar(statement)


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


def _base_offer_statement(publish_version: str) -> object:
    return (
        select(PublishedOffer, PublishedOfferPrice)
        .join(
            PublishedOfferPrice,
            and_(
                PublishedOfferPrice.publish_version == PublishedOffer.publish_version,
                PublishedOfferPrice.offer_code == PublishedOffer.offer_code,
            ),
        )
        .where(PublishedOffer.publish_version == publish_version)
        .where(PublishedOffer.display_status == "visible")
        .where(PublishedOffer.sell_status == "sellable")
        .where(*_active_price_filters())
        .order_by(PublishedOfferPrice.priority, PublishedOfferPrice.id, PublishedOffer.id)
    )


def resolve_active_offer(
    session: Session,
    offer_code: str,
) -> PublishedOfferPriceRow | None:
    publish_version = latest_offer_publish_version(session)
    if publish_version is None:
        return None

    statement = _base_offer_statement(publish_version).where(
        PublishedOffer.offer_code == offer_code
    )
    return session.execute(statement).first()


def list_active_offers_by_code(
    session: Session,
    offer_codes: list[str],
) -> dict[str, PublishedOfferPriceRow]:
    publish_version = latest_offer_publish_version(session)
    if publish_version is None or not offer_codes:
        return {}

    unique_offer_codes = list(dict.fromkeys(offer_codes))
    statement = _base_offer_statement(publish_version).where(
        PublishedOffer.offer_code.in_(unique_offer_codes)
    )

    result: dict[str, PublishedOfferPriceRow] = {}
    for offer, price in session.execute(statement).all():
        result.setdefault(offer.offer_code, (offer, price))
    return result
