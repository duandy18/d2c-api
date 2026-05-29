"""Storefront home service backed by Slot-first site configuration."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.domains.published.models.published import PublishedOffer, PublishedOfferPrice
from app.domains.site_config.contracts.storefront_home_contract import (
    StorefrontHomeOffer,
    StorefrontHomeOfferPosition,
    StorefrontHomePage,
    StorefrontHomeResponse,
    StorefrontHomeSlot,
    StorefrontHomeSlotItem,
    StorefrontSiteSummary,
    StorefrontTheme,
)
from app.domains.site_config.models import (
    OfferDisplayMetric,
    StorefrontPage,
    StorefrontPageSlot,
    StorefrontSite,
    StorefrontSlotItem,
    StorefrontSlotOfferPosition,
    StorefrontThemeSetting,
)
from app.domains.site_config.repos.storefront_offer_hydration_repo import (
    list_active_offers_by_code,
)
from app.domains.site_config.repos.storefront_site_config_repo import (
    get_active_theme,
    get_page,
    get_site,
    list_items_by_slot_ids,
    list_offer_display_metrics_by_offer_codes,
    list_offer_positions_by_slot_ids,
    list_slots,
)


def _json_record(value: dict[str, Any] | None) -> dict[str, Any]:
    return dict(value or {})


def _theme_schema(theme: StorefrontThemeSetting | None) -> StorefrontTheme | None:
    if theme is None:
        return None

    return StorefrontTheme(
        theme_code=theme.theme_code,
        primary_color=theme.primary_color,
        secondary_color=theme.secondary_color,
        background_color=theme.background_color,
        text_color=theme.text_color,
        font_family=theme.font_family,
        corner_radius=theme.corner_radius,
        button_style=theme.button_style,
    )


def _site_schema(
    site: StorefrontSite,
    theme: StorefrontThemeSetting | None,
) -> StorefrontSiteSummary:
    return StorefrontSiteSummary(
        site_code=site.site_code,
        site_name=site.site_name,
        brand_name=site.brand_name,
        logo_url=site.logo_url,
        default_currency=site.default_currency,
        theme=_theme_schema(theme),
    )


def _item_schema(item: StorefrontSlotItem) -> StorefrontHomeSlotItem:
    return StorefrontHomeSlotItem(
        item_code=item.item_code,
        item_type=item.item_type,
        label=item.label,
        title=item.title,
        subtitle=item.subtitle,
        description=item.description,
        icon=item.icon,
        image_url=item.image_url,
        link_type=item.link_type,
        link_value=item.link_value,
        payload=_json_record(item.payload_json),
        sort_order=item.sort_order,
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _offer_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _display_stock_status(
    display_metric: OfferDisplayMetric | None,
    fallback: str,
) -> str:
    if display_metric is None or not display_metric.is_active:
        return "out_of_stock"

    if display_metric.display_stock_quantity <= 0:
        return "out_of_stock"

    return fallback or "in_stock"


def _offer_schema(
    offer: PublishedOffer,
    price: PublishedOfferPrice,
    display_metric: OfferDisplayMetric | None,
) -> StorefrontHomeOffer:
    return StorefrontHomeOffer(
        offer_code=offer.offer_code,
        offer_type=getattr(offer, "offer_type", "single"),
        title=offer.title,
        subtitle=getattr(offer, "subtitle", None),
        description=getattr(offer, "description", None),
        image_url=getattr(offer, "image_url", None),
        price_code=price.price_code,
        price_cents=int(price.price_cents),
        compare_at_price_cents=_optional_int(getattr(price, "compare_at_price_cents", None)),
        currency=price.currency,
        promotion_badge=getattr(offer, "promotion_badge", None),
        sold_quantity=(
            display_metric.display_sold_quantity
            if display_metric is not None and display_metric.is_active
            else 0
        ),
        paid_customer_count=(
            display_metric.display_paid_customer_count
            if display_metric is not None and display_metric.is_active
            else 0
        ),
        display_stock_quantity=(
            display_metric.display_stock_quantity
            if display_metric is not None and display_metric.is_active
            else 0
        ),
        rating_score=_optional_float(getattr(offer, "rating_score", None)),
        review_count=_optional_int(getattr(offer, "review_count", None)),
        review_summary=getattr(offer, "review_summary", None),
        tags=_offer_tags(getattr(offer, "tags", None)),
        stock_status=_display_stock_status(
            display_metric,
            getattr(offer, "stock_status", "in_stock"),
        ),
        sell_status=offer.sell_status,
    )


def _position_visible(position: StorefrontSlotOfferPosition) -> bool:
    if not position.is_active:
        return False

    now = datetime.now(UTC)

    if position.visible_from is not None and position.visible_from > now:
        return False

    if position.visible_until is not None and position.visible_until <= now:
        return False

    return True


def _position_schema(
    position: StorefrontSlotOfferPosition,
    offer: StorefrontHomeOffer,
) -> StorefrontHomeOfferPosition:
    return StorefrontHomeOfferPosition(
        position_code=position.position_code,
        offer_code=position.offer_code,
        position_type=position.position_type,
        is_featured=position.is_featured,
        sort_order=position.sort_order,
        offer=offer,
    )


def _page_schema(
    page: StorefrontPage,
    slots: list[StorefrontHomeSlot],
) -> StorefrontHomePage:
    return StorefrontHomePage(
        page_code=page.page_code,
        page_type=page.page_type,
        route_path=page.route_path,
        title=page.title,
        description=page.description,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        slots=slots,
    )


def _slot_schema(
    slot: StorefrontPageSlot,
    items: list[StorefrontSlotItem],
    positions: list[StorefrontSlotOfferPosition],
    hydrated_offers: dict[str, tuple[PublishedOffer, PublishedOfferPrice]],
    display_metrics: dict[str, OfferDisplayMetric],
) -> StorefrontHomeSlot:
    active_items = [item for item in items if item.is_active]
    offer_positions: list[StorefrontHomeOfferPosition] = []

    for position in positions:
        if not _position_visible(position):
            continue

        row = hydrated_offers.get(position.offer_code)
        if row is None:
            continue

        offer, price = row
        offer_positions.append(
            _position_schema(
                position,
                _offer_schema(offer, price, display_metrics.get(position.offer_code)),
            )
        )

    return StorefrontHomeSlot(
        slot_code=slot.slot_code,
        slot_type=slot.slot_type,
        slot_group=slot.slot_group,
        title=slot.title,
        subtitle=slot.subtitle,
        content=_json_record(slot.content_json),
        presentation=_json_record(slot.presentation_json),
        sort_order=slot.sort_order,
        items=[_item_schema(item) for item in active_items],
        offers=offer_positions,
    )


def get_storefront_home(session: Session) -> StorefrontHomeResponse:
    site = get_site(session)
    if site is None or site.status != "active":
        return StorefrontHomeResponse(slot_count=0, item_count=0, offer_count=0)

    page = get_page(session, site.id, "home")
    if page is None or page.status != "active":
        return StorefrontHomeResponse(
            site=_site_schema(site, get_active_theme(session, site.id)),
            slot_count=0,
            item_count=0,
            offer_count=0,
        )

    slots = [slot for slot in list_slots(session, page.id) if slot.is_active]
    slot_ids = [slot.id for slot in slots]
    items_by_slot = list_items_by_slot_ids(session, slot_ids)
    positions_by_slot = list_offer_positions_by_slot_ids(session, slot_ids)

    offer_codes = [
        position.offer_code
        for slot_positions in positions_by_slot.values()
        for position in slot_positions
        if _position_visible(position)
    ]
    hydrated_offers = list_active_offers_by_code(session, offer_codes)
    display_metrics = list_offer_display_metrics_by_offer_codes(session, offer_codes)

    slot_schemas = [
        _slot_schema(
            slot=slot,
            items=items_by_slot.get(slot.id, []),
            positions=positions_by_slot.get(slot.id, []),
            hydrated_offers=hydrated_offers,
            display_metrics=display_metrics,
        )
        for slot in slots
    ]

    item_count = sum(len(slot.items) for slot in slot_schemas)
    offer_count = sum(len(slot.offers) for slot in slot_schemas)

    return StorefrontHomeResponse(
        site=_site_schema(site, get_active_theme(session, site.id)),
        page=_page_schema(page, slot_schemas),
        slot_count=len(slot_schemas),
        item_count=item_count,
        offer_count=offer_count,
    )
