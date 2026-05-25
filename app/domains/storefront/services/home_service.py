"""Storefront home service."""

from sqlalchemy.orm import Session

from app.domains.published.models.published import (
    PublishedGroup,
    PublishedOffer,
    PublishedOfferPosition,
    PublishedOfferPrice,
    PublishedStorefrontSection,
    PublishedStorefrontSectionLayout,
)
from app.domains.storefront.contracts.home_contract import (
    StorefrontHomeGroup,
    StorefrontHomeOfferCard,
    StorefrontHomeResponse,
    StorefrontHomeSection,
    StorefrontHomeSectionLayout,
)
from app.domains.storefront.repos.home_repo import (
    latest_storefront_publish_version,
    list_home_groups,
    list_home_layouts,
    list_home_rows,
    list_home_sections,
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


def _display_style_from_display_type(display_type: str) -> str:
    if display_type == "ranking_list":
        return "ranking"
    if display_type in {"banner", "promo_strip"}:
        return "banner"
    if display_type == "horizontal_scroll":
        return "list"
    return "grid"


def _default_display_type(group_kind: str) -> str:
    if group_kind == "hot":
        return "ranking_list"
    if group_kind == "bundle":
        return "featured_grid"
    if group_kind == "new":
        return "horizontal_scroll"
    if group_kind == "banner":
        return "banner"
    return "product_grid"


def _default_layout(group_kind: str) -> StorefrontHomeSectionLayout:
    display_type = _default_display_type(group_kind)

    if display_type == "ranking_list":
        return StorefrontHomeSectionLayout(
            display_type="ranking_list",
            columns_desktop=1,
            columns_tablet=1,
            columns_mobile=1,
            card_size="compact",
            image_ratio="1:1",
            show_promotion_badge=True,
            show_sales_summary=True,
            show_review_summary=True,
            show_compare_price=True,
            show_quantity_stepper=True,
            max_items=10,
        )

    if display_type == "featured_grid":
        return StorefrontHomeSectionLayout(
            display_type="featured_grid",
            columns_desktop=2,
            columns_tablet=2,
            columns_mobile=1,
            card_size="large",
            image_ratio="4:3",
            show_promotion_badge=True,
            show_sales_summary=True,
            show_review_summary=True,
            show_compare_price=True,
            show_quantity_stepper=True,
            max_items=8,
        )

    if display_type == "horizontal_scroll":
        return StorefrontHomeSectionLayout(
            display_type="horizontal_scroll",
            columns_desktop=4,
            columns_tablet=2,
            columns_mobile=1,
            card_size="standard",
            image_ratio="1:1",
            show_promotion_badge=True,
            show_sales_summary=True,
            show_review_summary=True,
            show_compare_price=True,
            show_quantity_stepper=True,
            max_items=12,
        )

    if display_type == "banner":
        return StorefrontHomeSectionLayout(
            display_type="banner",
            columns_desktop=1,
            columns_tablet=1,
            columns_mobile=1,
            card_size="large",
            image_ratio="16:9",
            show_promotion_badge=False,
            show_sales_summary=False,
            show_review_summary=False,
            show_compare_price=False,
            show_quantity_stepper=False,
            max_items=1,
        )

    return StorefrontHomeSectionLayout(
        display_type="product_grid",
        columns_desktop=4,
        columns_tablet=2,
        columns_mobile=1,
        card_size="standard",
        image_ratio="1:1",
        show_promotion_badge=True,
        show_sales_summary=True,
        show_review_summary=True,
        show_compare_price=True,
        show_quantity_stepper=True,
        max_items=12,
    )


def _layout_schema(
    layout: PublishedStorefrontSectionLayout | None,
    group_kind: str,
) -> StorefrontHomeSectionLayout:
    if layout is None:
        return _default_layout(group_kind)

    return StorefrontHomeSectionLayout(
        display_type=layout.display_type,
        columns_desktop=layout.columns_desktop,
        columns_tablet=layout.columns_tablet,
        columns_mobile=layout.columns_mobile,
        card_size=layout.card_size,
        image_ratio=layout.image_ratio,
        show_promotion_badge=layout.show_promotion_badge,
        show_sales_summary=layout.show_sales_summary,
        show_review_summary=layout.show_review_summary,
        show_compare_price=layout.show_compare_price,
        show_quantity_stepper=layout.show_quantity_stepper,
        max_items=layout.max_items,
    )


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


def _group_offers(
    rows: list[tuple[PublishedGroup, PublishedOfferPosition, PublishedOffer, PublishedOfferPrice]],
) -> dict[str, list[StorefrontHomeOfferCard]]:
    offers_by_group: dict[str, list[StorefrontHomeOfferCard]] = {}
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

    return offers_by_group


def _section_group_kind(
    section: PublishedStorefrontSection,
    groups_by_code: dict[str, PublishedGroup],
) -> str:
    if section.group_code is None:
        return "manual"

    group = groups_by_code.get(section.group_code)
    if group is None:
        return "manual"

    return group.group_kind


def _section_group_name(
    section: PublishedStorefrontSection,
    groups_by_code: dict[str, PublishedGroup],
) -> str | None:
    if section.group_code is None:
        return None

    group = groups_by_code.get(section.group_code)
    if group is None:
        return None

    return group.group_name


def _build_sections_from_published_sections(
    *,
    groups_by_code: dict[str, PublishedGroup],
    sections: list[PublishedStorefrontSection],
    layouts_by_section: dict[str, PublishedStorefrontSectionLayout],
    offers_by_group: dict[str, list[StorefrontHomeOfferCard]],
) -> list[StorefrontHomeSection]:
    result: list[StorefrontHomeSection] = []

    for section in sections:
        group_kind = _section_group_kind(section, groups_by_code)
        layout = _layout_schema(layouts_by_section.get(section.section_code), group_kind)
        offers = offers_by_group.get(section.group_code or "", [])
        if layout.max_items is not None:
            offers = offers[: layout.max_items]

        result.append(
            StorefrontHomeSection(
                section_code=section.section_code,
                section_type=section.section_type,
                group_code=section.group_code,
                group_name=_section_group_name(section, groups_by_code),
                title=section.title,
                subtitle=section.subtitle,
                description=section.description,
                display_style=_display_style_from_display_type(layout.display_type),
                sort_order=section.sort_order,
                layout=layout,
                offers=offers,
            )
        )

    return result


def _build_fallback_sections(
    *,
    groups: list[PublishedGroup],
    offers_by_group: dict[str, list[StorefrontHomeOfferCard]],
) -> list[StorefrontHomeSection]:
    result: list[StorefrontHomeSection] = []

    for group in groups:
        layout = _default_layout(group.group_kind)
        offers = offers_by_group.get(group.group_code, [])
        if layout.max_items is not None:
            offers = offers[: layout.max_items]

        result.append(
            StorefrontHomeSection(
                section_code=group.group_code,
                section_type="offer_shelf",
                group_code=group.group_code,
                group_name=group.group_name,
                title=group.group_name,
                subtitle=None,
                description=group.description,
                display_style=_display_style_from_display_type(layout.display_type),
                sort_order=group.sort_order,
                layout=layout,
                offers=offers,
            )
        )

    return result


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
    groups_by_code = {group.group_code: group for group in groups}
    rows = list_home_rows(session, publish_version)
    offers_by_group = _group_offers(rows)

    published_sections = list_home_sections(session, publish_version)
    layouts_by_section = {
        layout.section_code: layout for layout in list_home_layouts(session, publish_version)
    }

    if published_sections:
        sections = _build_sections_from_published_sections(
            groups_by_code=groups_by_code,
            sections=published_sections,
            layouts_by_section=layouts_by_section,
            offers_by_group=offers_by_group,
        )
    else:
        sections = _build_fallback_sections(groups=groups, offers_by_group=offers_by_group)

    sections = [
        section
        for section in sections
        if section.offers or section.layout.display_type in {"banner", "promo_strip"}
    ]
    offer_count = sum(len(section.offers) for section in sections)

    visible_group_codes = {
        section.group_code for section in sections if section.group_code is not None
    }
    visible_groups = [group for group in groups if group.group_code in visible_group_codes]

    return StorefrontHomeResponse(
        publish_version=publish_version,
        group_count=len(visible_groups),
        section_count=len(sections),
        offer_count=offer_count,
        groups=[_group_schema(group) for group in visible_groups],
        sections=sections,
    )
