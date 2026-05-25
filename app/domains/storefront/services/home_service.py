"""Storefront home service."""

from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPosition,
    PublishedOfferPrice,
)
from app.domains.storefront.contracts.home_contract import (
    StorefrontHomeGroup,
    StorefrontHomeOfferCard,
    StorefrontHomeResponse,
    StorefrontHomeSection,
)
from app.domains.storefront.repos.home_repo import (
    latest_storefront_publish_version,
    list_home_groups,
    list_home_rows,
)


def _group_schema(group: PublishedGroup) -> StorefrontHomeGroup:
    return StorefrontHomeGroup(
        group_code=group.group_code,
        group_name=group.group_name,
        group_kind=group.group_kind,
        description=group.description,
        image_url=group.image_url,
        sort_order=group.sort_order,
    )


def _display_style(group: PublishedGroup) -> str:
    if group.group_kind == "hot":
        return "ranking"
    if group.group_kind == "banner":
        return "banner"
    return "grid"


def _offer_tags(
    group: PublishedGroup,
    offer: PublishedOffer,
) -> list[str]:
    tags: list[str] = []

    if group.group_name:
        tags.append(group.group_name)

    if offer.offer_type:
        tags.append(offer.offer_type)

    return tags


def _offer_card_schema(
    *,
    group: PublishedGroup,
    position: PublishedOfferPosition,
    offer: PublishedOffer,
    price: PublishedOfferPrice,
) -> StorefrontHomeOfferCard:
    return StorefrontHomeOfferCard(
        offer_code=offer.offer_code,
        offer_type=offer.offer_type,
        title=offer.title,
        subtitle=offer.subtitle,
        description=offer.description,
        image_url=offer.image_url,
        group_code=group.group_code,
        group_name=group.group_name,
        position_code=position.position_code,
        position_sort_order=position.sort_order,
        is_featured=position.is_featured,
        price_code=price.price_code,
        price_cents=price.price_cents,
        compare_at_price_cents=price.compare_at_price_cents,
        currency=price.currency,
        promotion_badge=None,
        sold_quantity=None,
        paid_customer_count=None,
        rating_score=None,
        review_count=None,
        review_summary=None,
        tags=_offer_tags(group, offer),
        stock_status="in_stock",
    )


def get_storefront_home(session: Session) -> StorefrontHomeResponse:
    publish_version = latest_storefront_publish_version(session)

    if publish_version is None:
        return StorefrontHomeResponse(
            publish_version=None,
            group_count=0,
            section_count=0,
            offer_count=0,
            groups=[],
            sections=[],
        )

    groups = list_home_groups(session, publish_version)
    rows = list_home_rows(session, publish_version)

    offers_by_group: dict[str, list[StorefrontHomeOfferCard]] = {
        group.group_code: [] for group in groups
    }
    seen_position_price: set[tuple[str, str]] = set()

    for group, position, offer, price in rows:
        dedupe_key = (position.position_code, offer.offer_code)
        if dedupe_key in seen_position_price:
            continue

        seen_position_price.add(dedupe_key)
        offers_by_group.setdefault(group.group_code, []).append(
            _offer_card_schema(
                group=group,
                position=position,
                offer=offer,
                price=price,
            )
        )

    sections = [
        StorefrontHomeSection(
            section_code=group.group_code,
            group_code=group.group_code,
            group_name=group.group_name,
            title=group.group_name,
            display_style=_display_style(group),
            sort_order=group.sort_order,
            offers=offers_by_group.get(group.group_code, []),
        )
        for group in groups
    ]

    offer_count = sum(len(section.offers) for section in sections)

    return StorefrontHomeResponse(
        publish_version=publish_version,
        group_count=len(groups),
        section_count=len(sections),
        offer_count=offer_count,
        groups=[_group_schema(group) for group in groups],
        sections=sections,
    )
