"""Backoffice site configuration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.site_config.contracts.backoffice_site_config_contract import (
    BackofficeHomeConfigResponse,
    BackofficeHomePagePatchRequest,
    BackofficeOfferDisplayMetricsRequest,
    BackofficeOfferDisplayMetricsResponse,
    BackofficeOfferResolveResponse,
    BackofficeSlotItemsPutRequest,
    BackofficeSlotOfferPositionsPutRequest,
    BackofficeSlotPatchRequest,
)
from app.domains.site_config.services.backoffice_site_config_service import (
    get_backoffice_home_config,
    get_offer_display_metrics,
    patch_home_page,
    patch_home_slot,
    replace_slot_items,
    replace_slot_offer_positions,
    resolve_offer_for_site_config,
    update_offer_display_metrics,
)

router = APIRouter(prefix="/backoffice/site-config", tags=["backoffice-site-config"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/pages/home", response_model=BackofficeHomeConfigResponse)
def get_home_config(session: SessionDep) -> BackofficeHomeConfigResponse:
    return get_backoffice_home_config(session)


@router.patch("/pages/home", response_model=BackofficeHomeConfigResponse)
def patch_home_config(
    request: BackofficeHomePagePatchRequest,
    session: SessionDep,
) -> BackofficeHomeConfigResponse:
    return patch_home_page(session, request)


@router.patch("/pages/home/slots/{slot_code}", response_model=BackofficeHomeConfigResponse)
def patch_home_slot_config(
    slot_code: str,
    request: BackofficeSlotPatchRequest,
    session: SessionDep,
) -> BackofficeHomeConfigResponse:
    return patch_home_slot(session, slot_code, request)


@router.put("/pages/home/slots/{slot_code}/items", response_model=BackofficeHomeConfigResponse)
def put_home_slot_items(
    slot_code: str,
    request: BackofficeSlotItemsPutRequest,
    session: SessionDep,
) -> BackofficeHomeConfigResponse:
    return replace_slot_items(session, slot_code, request)


@router.put(
    "/pages/home/slots/{slot_code}/offer-positions",
    response_model=BackofficeHomeConfigResponse,
)
def put_home_slot_offer_positions(
    slot_code: str,
    request: BackofficeSlotOfferPositionsPutRequest,
    session: SessionDep,
) -> BackofficeHomeConfigResponse:
    return replace_slot_offer_positions(session, slot_code, request)


@router.get("/offers/{offer_code}/resolve", response_model=BackofficeOfferResolveResponse)
def resolve_home_offer(
    offer_code: str,
    session: SessionDep,
) -> BackofficeOfferResolveResponse:
    return resolve_offer_for_site_config(session, offer_code)

@router.get(
    "/offers/{offer_code}/display-metrics",
    response_model=BackofficeOfferDisplayMetricsResponse,
)
def get_offer_display_metrics_route(
    offer_code: str,
    session: SessionDep,
) -> BackofficeOfferDisplayMetricsResponse:
    return get_offer_display_metrics(session, offer_code)


@router.patch(
    "/offers/{offer_code}/display-metrics",
    response_model=BackofficeOfferDisplayMetricsResponse,
)
def patch_offer_display_metrics_route(
    offer_code: str,
    payload: BackofficeOfferDisplayMetricsRequest,
    session: SessionDep,
) -> BackofficeOfferDisplayMetricsResponse:
    return update_offer_display_metrics(session, offer_code, payload)
