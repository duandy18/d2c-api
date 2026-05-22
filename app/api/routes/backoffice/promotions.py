"""Backoffice promotion routes; HTTP paths are /backoffice/promotions/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.promotions.contracts.backoffice_promotion_contract import (
    BackofficeCouponsResponse,
    BackofficeCustomerCouponsResponse,
    BackofficePromotion,
    BackofficePromotionCreateRequest,
    BackofficePromotionHealthResponse,
    BackofficePromotionsResponse,
    BackofficePromotionTargetsResponse,
)
from app.domains.promotions.services.backoffice_promotion_service import (
    BackofficePromotionDuplicateCodeError,
    BackofficePromotionInvalidRangeError,
    BackofficePromotionNotFoundError,
    activate_backoffice_promotion,
    create_backoffice_promotion,
    deactivate_backoffice_promotion,
    get_backoffice_coupons,
    get_backoffice_customer_coupons,
    get_backoffice_promotion_targets,
    get_backoffice_promotions,
)

router = APIRouter(prefix="/backoffice/promotions", tags=["backoffice-promotions"])
SessionDep = Annotated[Session, Depends(get_session)]


def require_backoffice_client(
    x_backoffice_client: Annotated[str | None, Header(alias="X-Backoffice-Client")] = None,
) -> None:
    if x_backoffice_client != "d2c-backoffice":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="backoffice_client_required",
        )


BackofficeClientDep = Annotated[None, Depends(require_backoffice_client)]


@router.get("/health", response_model=BackofficePromotionHealthResponse)
def backoffice_promotions_health(_: BackofficeClientDep) -> BackofficePromotionHealthResponse:
    return BackofficePromotionHealthResponse(
        status="ok",
        module="backoffice_promotions",
        surface="merchant_management",
    )


@router.get("", response_model=BackofficePromotionsResponse)
def backoffice_promotions_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePromotionsResponse:
    return get_backoffice_promotions(session)


@router.post(
    "",
    response_model=BackofficePromotion,
    status_code=status.HTTP_201_CREATED,
)
def backoffice_promotions_create(
    payload: BackofficePromotionCreateRequest,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePromotion:
    try:
        return create_backoffice_promotion(session, payload)
    except BackofficePromotionDuplicateCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except BackofficePromotionInvalidRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{promotion_code}/activate", response_model=BackofficePromotion)
def backoffice_promotions_activate(
    promotion_code: str,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePromotion:
    try:
        return activate_backoffice_promotion(session, promotion_code)
    except BackofficePromotionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{promotion_code}/deactivate", response_model=BackofficePromotion)
def backoffice_promotions_deactivate(
    promotion_code: str,
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePromotion:
    try:
        return deactivate_backoffice_promotion(session, promotion_code)
    except BackofficePromotionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/targets", response_model=BackofficePromotionTargetsResponse)
def backoffice_promotion_targets_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePromotionTargetsResponse:
    return get_backoffice_promotion_targets(session)


@router.get("/coupons", response_model=BackofficeCouponsResponse)
def backoffice_coupons_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeCouponsResponse:
    return get_backoffice_coupons(session)


@router.get("/customer-coupons", response_model=BackofficeCustomerCouponsResponse)
def backoffice_customer_coupons_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeCustomerCouponsResponse:
    return get_backoffice_customer_coupons(session)
