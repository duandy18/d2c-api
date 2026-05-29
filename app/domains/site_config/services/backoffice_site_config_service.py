"""Backoffice site configuration service."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.site_config.contracts.backoffice_site_config_contract import (
    BackofficeHomeConfigResponse,
    BackofficeHomePage,
    BackofficeHomePagePatchRequest,
    BackofficeOfferDisplayMetricsRequest,
    BackofficeOfferDisplayMetricsResponse,
    BackofficeOfferResolveResponse,
    BackofficePageSlot,
    BackofficeSlotItemPut,
    BackofficeSlotItemsPutRequest,
    BackofficeSlotOfferPosition,
    BackofficeSlotOfferPositionPut,
    BackofficeSlotOfferPositionsPutRequest,
    BackofficeSlotPatchRequest,
    BackofficeValidationIssue,
)
from app.domains.site_config.contracts.storefront_home_contract import (
    StorefrontHomeOffer,
    StorefrontHomeSlotItem,
)
from app.domains.site_config.models import (
    OfferDisplayMetric,
    StorefrontPage,
    StorefrontPageSlot,
    StorefrontSlotItem,
    StorefrontSlotOfferPosition,
)
from app.domains.site_config.repos.storefront_offer_hydration_repo import (
    list_active_offers_by_code,
    resolve_active_offer,
)
from app.domains.site_config.repos.storefront_site_config_repo import (
    delete_slot_items,
    delete_slot_offer_positions,
    get_active_theme,
    get_offer_display_metric,
    get_page,
    get_site,
    get_slot,
    list_items_by_slot_ids,
    list_offer_display_metrics_by_offer_codes,
    list_offer_positions_by_slot_ids,
    list_slots,
    upsert_offer_display_metric,
)
from app.domains.site_config.services.slot_registry import (
    get_home_slot_spec,
    require_home_slot_spec,
)
from app.domains.site_config.services.storefront_home_service import (
    _offer_schema,
    _site_schema,
)


def _json_record(value: dict[str, object] | None) -> dict[str, object]:
    return dict(value or {})


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


def _offer_position_issue(
    slot_code: str,
    offer_code: str,
) -> BackofficeValidationIssue:
    return BackofficeValidationIssue(
        level="error",
        code="site_config_offer_not_sellable",
        message=f"已配置的上架商品不可售或缺少有效前台价格：{offer_code}",
        slot_code=slot_code,
        field_key="offer_code",
        offer_code=offer_code,
    )


def _page_response(page: StorefrontPage, slots: list[BackofficePageSlot]) -> BackofficeHomePage:
    return BackofficeHomePage(
        page_code=page.page_code,
        page_type=page.page_type,
        route_path=page.route_path,
        title=page.title,
        description=page.description,
        status=page.status,
        seo_title=page.seo_title,
        seo_description=page.seo_description,
        slots=slots,
    )


def _position_response(
    slot: StorefrontPageSlot,
    position: StorefrontSlotOfferPosition,
    offer: StorefrontHomeOffer | None,
) -> BackofficeSlotOfferPosition:
    issues = (
        []
        if offer is not None
        else [_offer_position_issue(slot.slot_code, position.offer_code)]
    )
    return BackofficeSlotOfferPosition(
        position_code=position.position_code,
        offer_code=position.offer_code,
        position_type=position.position_type,
        is_featured=position.is_featured,
        sort_order=position.sort_order,
        is_active=position.is_active,
        visible_from=position.visible_from,
        visible_until=position.visible_until,
        offer=offer,
        validation_issues=issues,
    )


def _slot_response(
    slot: StorefrontPageSlot,
    items: list[StorefrontSlotItem],
    positions: list[StorefrontSlotOfferPosition],
    hydrated_offers: dict[str, StorefrontHomeOffer],
) -> BackofficePageSlot:
    spec = get_home_slot_spec(slot.slot_code)
    supports_items = spec.supports_items if spec else False
    supports_offers = spec.supports_offers if spec else False

    return BackofficePageSlot(
        slot_code=slot.slot_code,
        slot_type=slot.slot_type,
        slot_group=slot.slot_group,
        title=slot.title,
        subtitle=slot.subtitle,
        content=_json_record(slot.content_json),
        presentation=_json_record(slot.presentation_json),
        sort_order=slot.sort_order,
        is_active=slot.is_active,
        supports_items=supports_items,
        supports_offers=supports_offers,
        items=[_item_schema(item) for item in items],
        offer_positions=[
            _position_response(slot, position, hydrated_offers.get(position.offer_code))
            for position in positions
        ],
    )


def _load_home_page(session: Session) -> StorefrontPage:
    site = get_site(session)
    if site is None:
        raise HTTPException(status_code=404, detail="site_config_site_not_found")

    page = get_page(session, site.id, "home")
    if page is None:
        raise HTTPException(status_code=404, detail="site_config_home_page_not_found")

    return page


def _load_home_slot(session: Session, slot_code: str) -> tuple[StorefrontPage, StorefrontPageSlot]:
    page = _load_home_page(session)
    slot = get_slot(session, page.id, slot_code)
    if slot is None:
        raise HTTPException(status_code=404, detail="site_config_slot_not_found")
    return page, slot


def get_backoffice_home_config(session: Session) -> BackofficeHomeConfigResponse:
    site = get_site(session)
    if site is None:
        return BackofficeHomeConfigResponse()

    page = get_page(session, site.id, "home")
    if page is None:
        return BackofficeHomeConfigResponse(
            site=_site_schema(site, get_active_theme(session, site.id)),
        )

    slots = list_slots(session, page.id)
    slot_ids = [slot.id for slot in slots]
    items_by_slot = list_items_by_slot_ids(session, slot_ids)
    positions_by_slot = list_offer_positions_by_slot_ids(session, slot_ids)

    offer_codes = [
        position.offer_code
        for slot_positions in positions_by_slot.values()
        for position in slot_positions
    ]
    hydrated_rows = list_active_offers_by_code(session, offer_codes)
    display_metrics = list_offer_display_metrics_by_offer_codes(session, offer_codes)
    hydrated_offers = {
        offer_code: _offer_schema(
            offer,
            price,
            display_metrics.get(offer_code),
        )
        for offer_code, (offer, price) in hydrated_rows.items()
    }

    slot_responses = [
        _slot_response(
            slot=slot,
            items=items_by_slot.get(slot.id, []),
            positions=positions_by_slot.get(slot.id, []),
            hydrated_offers=hydrated_offers,
        )
        for slot in slots
    ]

    validation_issues = [
        issue
        for slot in slot_responses
        for position in slot.offer_positions
        for issue in position.validation_issues
    ]

    return BackofficeHomeConfigResponse(
        site=_site_schema(site, get_active_theme(session, site.id)),
        page=_page_response(page, slot_responses),
        validation_issues=validation_issues,
    )


def patch_home_page(
    session: Session,
    request: BackofficeHomePagePatchRequest,
) -> BackofficeHomeConfigResponse:
    page = _load_home_page(session)

    if request.title is not None:
        page.title = request.title
    if request.description is not None:
        page.description = request.description
    if request.status is not None:
        page.status = request.status
    if request.seo_title is not None:
        page.seo_title = request.seo_title
    if request.seo_description is not None:
        page.seo_description = request.seo_description

    session.commit()
    return get_backoffice_home_config(session)


def patch_home_slot(
    session: Session,
    slot_code: str,
    request: BackofficeSlotPatchRequest,
) -> BackofficeHomeConfigResponse:
    require_home_slot_spec(slot_code)
    _, slot = _load_home_slot(session, slot_code)

    if request.title is not None:
        slot.title = request.title
    if request.subtitle is not None:
        slot.subtitle = request.subtitle
    if request.content is not None:
        slot.content_json = request.content
    if request.presentation is not None:
        slot.presentation_json = request.presentation
    if request.sort_order is not None:
        slot.sort_order = request.sort_order
    if request.is_active is not None:
        slot.is_active = request.is_active

    session.commit()
    return get_backoffice_home_config(session)


def replace_slot_items(
    session: Session,
    slot_code: str,
    request: BackofficeSlotItemsPutRequest,
) -> BackofficeHomeConfigResponse:
    spec = require_home_slot_spec(slot_code)
    if not spec.supports_items:
        raise HTTPException(status_code=422, detail="site_config_slot_does_not_accept_items")

    _, slot = _load_home_slot(session, slot_code)

    item_codes = [item.item_code for item in request.items]
    if len(item_codes) != len(set(item_codes)):
        raise HTTPException(status_code=422, detail="site_config_duplicate_item_code")

    delete_slot_items(session, slot.id)

    for item in request.items:
        session.add(_item_from_request(slot.id, item))

    session.commit()
    return get_backoffice_home_config(session)


def _item_from_request(slot_id: int, item: BackofficeSlotItemPut) -> StorefrontSlotItem:
    return StorefrontSlotItem(
        slot_id=slot_id,
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
        payload_json=item.payload,
        sort_order=item.sort_order,
        is_active=item.is_active,
    )


def replace_slot_offer_positions(
    session: Session,
    slot_code: str,
    request: BackofficeSlotOfferPositionsPutRequest,
) -> BackofficeHomeConfigResponse:
    spec = require_home_slot_spec(slot_code)
    if not spec.supports_offers:
        raise HTTPException(
            status_code=422,
            detail="site_config_slot_does_not_accept_offer_positions",
        )

    _, slot = _load_home_slot(session, slot_code)

    position_codes = [position.position_code for position in request.offer_positions]
    offer_codes = [position.offer_code for position in request.offer_positions]

    if len(position_codes) != len(set(position_codes)):
        raise HTTPException(status_code=422, detail="site_config_duplicate_position_code")

    if len(offer_codes) != len(set(offer_codes)):
        raise HTTPException(status_code=422, detail="site_config_duplicate_offer_code")

    for offer_code in offer_codes:
        if resolve_active_offer(session, offer_code) is None:
            raise HTTPException(status_code=422, detail="site_config_offer_not_sellable")

    delete_slot_offer_positions(session, slot.id)

    for position in request.offer_positions:
        session.add(_position_from_request(slot.id, position))

    session.commit()
    return get_backoffice_home_config(session)


def _position_from_request(
    slot_id: int,
    position: BackofficeSlotOfferPositionPut,
) -> StorefrontSlotOfferPosition:
    return StorefrontSlotOfferPosition(
        slot_id=slot_id,
        position_code=position.position_code,
        offer_code=position.offer_code,
        position_type=position.position_type,
        is_featured=position.is_featured,
        sort_order=position.sort_order,
        is_active=position.is_active,
        visible_from=position.visible_from,
        visible_until=position.visible_until,
    )


def resolve_offer_for_site_config(
    session: Session,
    offer_code: str,
) -> BackofficeOfferResolveResponse:
    row = resolve_active_offer(session, offer_code)
    if row is None:
        raise HTTPException(status_code=404, detail="site_config_offer_not_found")

    offer, price = row
    return BackofficeOfferResolveResponse(
        offer=_offer_schema(offer, price),
        raw={"offer_code": offer_code},
    )

def _display_metrics_response(
    offer_code: str,
    metric: OfferDisplayMetric | None,
) -> BackofficeOfferDisplayMetricsResponse:
    return BackofficeOfferDisplayMetricsResponse(
        offer_code=offer_code,
        display_sold_quantity=metric.display_sold_quantity if metric is not None else 0,
        display_paid_customer_count=(
            metric.display_paid_customer_count if metric is not None else 0
        ),
        display_stock_quantity=metric.display_stock_quantity if metric is not None else 0,
        is_active=metric.is_active if metric is not None else True,
    )


def get_offer_display_metrics(
    session: Session,
    offer_code: str,
) -> BackofficeOfferDisplayMetricsResponse:
    if resolve_active_offer(session, offer_code) is None:
        raise HTTPException(status_code=404, detail="site_config_offer_not_found")

    return _display_metrics_response(
        offer_code,
        get_offer_display_metric(session, offer_code),
    )


def update_offer_display_metrics(
    session: Session,
    offer_code: str,
    request: BackofficeOfferDisplayMetricsRequest,
) -> BackofficeOfferDisplayMetricsResponse:
    if resolve_active_offer(session, offer_code) is None:
        raise HTTPException(status_code=404, detail="site_config_offer_not_found")

    metric = get_offer_display_metric(session, offer_code)
    if metric is None:
        metric = OfferDisplayMetric(offer_code=offer_code)

    metric.display_sold_quantity = request.display_sold_quantity
    metric.display_paid_customer_count = request.display_paid_customer_count
    metric.display_stock_quantity = request.display_stock_quantity
    metric.is_active = request.is_active

    saved = upsert_offer_display_metric(session, metric)
    session.commit()

    return _display_metrics_response(offer_code, saved)
