"""Storefront home service."""

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
from app.domains.storefront.contracts.home_contract import (
    StorefrontHomeBlock,
    StorefrontHomeBlockLayout,
    StorefrontHomeBlockPosition,
    StorefrontHomeOffer,
    StorefrontHomePage,
    StorefrontHomeRegion,
    StorefrontHomeResponse,
)
from app.domains.storefront.repos.home_repo import (
    get_home_page,
    latest_client_home_publish_version,
    list_home_action_policies,
    list_home_data_bindings,
    list_home_layouts,
    list_home_regions,
    list_home_rows,
    list_home_sections,
    list_home_tracking_policies,
    list_home_visibility_rules,
)


def _default_display_type(section_type: str) -> str:
    if section_type == "ranking":
        return "ranking_list"
    if section_type == "hero":
        return "banner"
    if section_type == "promo":
        return "promo_strip"
    return "product_grid"


def _default_layout(section_type: str) -> StorefrontHomeBlockLayout:
    display_type = _default_display_type(section_type)

    if display_type == "ranking_list":
        return StorefrontHomeBlockLayout(
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

    if display_type == "banner":
        return StorefrontHomeBlockLayout(
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

    if display_type == "promo_strip":
        return StorefrontHomeBlockLayout(
            display_type="promo_strip",
            columns_desktop=1,
            columns_tablet=1,
            columns_mobile=1,
            card_size="compact",
            image_ratio="16:9",
            show_promotion_badge=True,
            show_sales_summary=False,
            show_review_summary=False,
            show_compare_price=False,
            show_quantity_stepper=False,
            max_items=1,
        )

    return StorefrontHomeBlockLayout(
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
    section_type: str,
) -> StorefrontHomeBlockLayout:
    if layout is None:
        return _default_layout(section_type)

    return StorefrontHomeBlockLayout(
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


def _offer_tags(offer: PublishedOffer) -> list[str]:
    tags: list[str] = []

    if offer.offer_type:
        tags.append(offer.offer_type)

    return tags


def _offer_schema(
    *,
    offer: PublishedOffer,
    price: PublishedOfferPrice,
) -> StorefrontHomeOffer:
    return StorefrontHomeOffer(
        offer_code=offer.offer_code,
        offer_type=offer.offer_type,
        title=offer.title,
        subtitle=offer.subtitle,
        description=offer.description,
        image_url=offer.image_url,
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
        tags=_offer_tags(offer),
        stock_status="in_stock",
    )


def _position_schema(
    *,
    position: PublishedStorefrontSectionPosition,
    offer: PublishedOffer,
    price: PublishedOfferPrice,
) -> StorefrontHomeBlockPosition:
    return StorefrontHomeBlockPosition(
        position_code=position.position_code,
        offer_code=position.offer_code,
        sort_order=position.sort_order,
        position_type=position.position_type,
        is_featured=position.is_featured,
        offer=_offer_schema(offer=offer, price=price),
    )


def _positions_by_section(
    rows: list[
        tuple[
            PublishedStorefrontSection,
            PublishedStorefrontSectionPosition,
            PublishedOffer,
            PublishedOfferPrice,
        ]
    ],
) -> dict[str, list[StorefrontHomeBlockPosition]]:
    result: dict[str, list[StorefrontHomeBlockPosition]] = {}
    seen_position_offer: set[tuple[str, str]] = set()

    for section, position, offer, price in rows:
        dedupe_key = (position.position_code, offer.offer_code)
        if dedupe_key in seen_position_offer:
            continue

        seen_position_offer.add(dedupe_key)
        result.setdefault(section.section_code, []).append(
            _position_schema(position=position, offer=offer, price=price)
        )

    return result


def _codes_by_target(
    rows: list[
        PublishedClientDataBinding
        | PublishedClientVisibilityRule
        | PublishedClientActionPolicy
        | PublishedClientTrackingPolicy
    ],
    code_attr: str,
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}

    for row in rows:
        if row.target_type != "block_type":
            continue

        code = getattr(row, code_attr)
        result.setdefault(row.target_code, []).append(code)

    return result


def _build_block(
    *,
    section: PublishedStorefrontSection,
    layout: PublishedStorefrontSectionLayout | None,
    positions: list[StorefrontHomeBlockPosition],
    data_binding_codes_by_block_type: dict[str, list[str]],
    visibility_rule_codes_by_block_type: dict[str, list[str]],
    action_policy_codes_by_block_type: dict[str, list[str]],
    tracking_policy_codes_by_block_type: dict[str, list[str]],
) -> StorefrontHomeBlock:
    layout_schema = _layout_schema(layout, section.section_type)
    limited_positions = positions
    if layout_schema.max_items is not None:
        limited_positions = positions[: layout_schema.max_items]

    return StorefrontHomeBlock(
        block_code=section.section_code,
        block_type=section.section_type,
        title=section.title,
        subtitle=section.subtitle,
        description=section.description,
        sort_order=section.sort_order,
        layout=layout_schema,
        data_binding_codes=data_binding_codes_by_block_type.get(section.section_type, []),
        visibility_rule_codes=visibility_rule_codes_by_block_type.get(section.section_type, []),
        action_policy_codes=action_policy_codes_by_block_type.get(section.section_type, []),
        tracking_policy_codes=tracking_policy_codes_by_block_type.get(section.section_type, []),
        positions=limited_positions,
    )


def _region_accepts_block(region: PublishedClientRegion, block_type: str) -> bool:
    return block_type in region.allowed_block_types


def _build_regions(
    *,
    regions: list[PublishedClientRegion],
    block_sections: list[PublishedStorefrontSection],
    layouts_by_section: dict[str, PublishedStorefrontSectionLayout],
    positions_by_section: dict[str, list[StorefrontHomeBlockPosition]],
    data_binding_codes_by_block_type: dict[str, list[str]],
    visibility_rule_codes_by_block_type: dict[str, list[str]],
    action_policy_codes_by_block_type: dict[str, list[str]],
    tracking_policy_codes_by_block_type: dict[str, list[str]],
) -> list[StorefrontHomeRegion]:
    blocks_by_region_code: dict[str, list[StorefrontHomeBlock]] = {
        region.region_code: [] for region in regions
    }

    for section in block_sections:
        region = next(
            (item for item in regions if _region_accepts_block(item, section.section_type)),
            None,
        )
        if region is None:
            continue

        current_blocks = blocks_by_region_code[region.region_code]
        if region.max_blocks is not None and len(current_blocks) >= region.max_blocks:
            continue

        positions = positions_by_section.get(section.section_code, [])
        layout = layouts_by_section.get(section.section_code)
        block = _build_block(
            section=section,
            layout=layout,
            positions=positions,
            data_binding_codes_by_block_type=data_binding_codes_by_block_type,
            visibility_rule_codes_by_block_type=visibility_rule_codes_by_block_type,
            action_policy_codes_by_block_type=action_policy_codes_by_block_type,
            tracking_policy_codes_by_block_type=tracking_policy_codes_by_block_type,
        )

        if block.positions or block.layout.display_type in {"banner", "promo_strip"}:
            current_blocks.append(block)

    return [
        StorefrontHomeRegion(
            region_code=region.region_code,
            region_type=region.region_type,
            title=region.title,
            description=region.description,
            sort_order=region.sort_order,
            allowed_block_types=region.allowed_block_types,
            blocks=blocks_by_region_code[region.region_code],
        )
        for region in regions
    ]


def _page_schema(
    *,
    page: PublishedClientPage,
    regions: list[StorefrontHomeRegion],
) -> StorefrontHomePage:
    return StorefrontHomePage(
        page_code=page.page_code,
        page_type=page.page_type,
        route_path=page.route_path,
        title=page.title,
        description=page.description,
        regions=regions,
    )


def get_storefront_home(session: Session) -> StorefrontHomeResponse:
    page_code = "home"
    surface_code = "web_desktop"
    publish_version = latest_client_home_publish_version(session, page_code)

    if publish_version is None:
        return StorefrontHomeResponse(
            publish_version=None,
            page_code=page_code,
            surface_code=surface_code,
            region_count=0,
            block_count=0,
            offer_count=0,
            page=None,
        )

    page = get_home_page(session, publish_version, page_code)
    if page is None:
        return StorefrontHomeResponse(
            publish_version=publish_version,
            page_code=page_code,
            surface_code=surface_code,
            region_count=0,
            block_count=0,
            offer_count=0,
            page=None,
        )

    regions = list_home_regions(session, publish_version, page.page_code)
    block_sections = list_home_sections(session, publish_version)
    layouts_by_section = {
        layout.section_code: layout for layout in list_home_layouts(session, publish_version)
    }
    positions_by_section = _positions_by_section(list_home_rows(session, publish_version))

    data_binding_codes_by_block_type = _codes_by_target(
        list_home_data_bindings(session, publish_version),
        "binding_code",
    )
    visibility_rule_codes_by_block_type = _codes_by_target(
        list_home_visibility_rules(session, publish_version),
        "rule_code",
    )
    action_policy_codes_by_block_type = _codes_by_target(
        list_home_action_policies(session, publish_version),
        "policy_code",
    )
    tracking_policy_codes_by_block_type = _codes_by_target(
        list_home_tracking_policies(session, publish_version),
        "policy_code",
    )

    home_regions = _build_regions(
        regions=regions,
        block_sections=block_sections,
        layouts_by_section=layouts_by_section,
        positions_by_section=positions_by_section,
        data_binding_codes_by_block_type=data_binding_codes_by_block_type,
        visibility_rule_codes_by_block_type=visibility_rule_codes_by_block_type,
        action_policy_codes_by_block_type=action_policy_codes_by_block_type,
        tracking_policy_codes_by_block_type=tracking_policy_codes_by_block_type,
    )
    page_schema = _page_schema(page=page, regions=home_regions)

    block_count = sum(len(region.blocks) for region in home_regions)
    offer_count = sum(len(block.positions) for region in home_regions for block in region.blocks)

    return StorefrontHomeResponse(
        publish_version=publish_version,
        page_code=page.page_code,
        surface_code=surface_code,
        region_count=len(home_regions),
        block_count=block_count,
        offer_count=offer_count,
        page=page_schema,
    )
