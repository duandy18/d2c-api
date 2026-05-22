from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.admin_promotion import (
    AdminCouponsResponse,
    AdminCustomerCouponsResponse,
    AdminPromotion,
    AdminPromotionCreateRequest,
    AdminPromotionHealthResponse,
    AdminPromotionsResponse,
    AdminPromotionTargetsResponse,
)
from app.services.admin_promotion_service import (
    AdminPromotionDuplicateCodeError,
    AdminPromotionInvalidRangeError,
    AdminPromotionNotFoundError,
    activate_admin_promotion,
    create_admin_promotion,
    deactivate_admin_promotion,
    get_admin_coupons,
    get_admin_customer_coupons,
    get_admin_promotion_targets,
    get_admin_promotions,
)

router = APIRouter(prefix="/admin/promotions", tags=["admin-promotions"])
SessionDep = Annotated[Session, Depends(get_session)]


def require_admin_client(
    x_admin_client: Annotated[str | None, Header(alias="X-Admin-Client")] = None,
) -> None:
    if x_admin_client != "d2c-admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="admin_client_required",
        )


AdminClientDep = Annotated[None, Depends(require_admin_client)]


@router.get("/health", response_model=AdminPromotionHealthResponse)
def admin_promotions_health(_: AdminClientDep) -> AdminPromotionHealthResponse:
    return AdminPromotionHealthResponse(
        status="ok",
        module="admin_promotions",
        surface="merchant_management",
    )


@router.get("", response_model=AdminPromotionsResponse)
def admin_promotions_list(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminPromotionsResponse:
    return get_admin_promotions(session)


@router.post(
    "",
    response_model=AdminPromotion,
    status_code=status.HTTP_201_CREATED,
)
def admin_promotions_create(
    payload: AdminPromotionCreateRequest,
    _: AdminClientDep,
    session: SessionDep,
) -> AdminPromotion:
    try:
        return create_admin_promotion(session, payload)
    except AdminPromotionDuplicateCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AdminPromotionInvalidRangeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{promotion_code}/activate", response_model=AdminPromotion)
def admin_promotions_activate(
    promotion_code: str,
    _: AdminClientDep,
    session: SessionDep,
) -> AdminPromotion:
    try:
        return activate_admin_promotion(session, promotion_code)
    except AdminPromotionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{promotion_code}/deactivate", response_model=AdminPromotion)
def admin_promotions_deactivate(
    promotion_code: str,
    _: AdminClientDep,
    session: SessionDep,
) -> AdminPromotion:
    try:
        return deactivate_admin_promotion(session, promotion_code)
    except AdminPromotionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/targets", response_model=AdminPromotionTargetsResponse)
def admin_promotion_targets_list(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminPromotionTargetsResponse:
    return get_admin_promotion_targets(session)


@router.get("/coupons", response_model=AdminCouponsResponse)
def admin_coupons_list(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminCouponsResponse:
    return get_admin_coupons(session)


@router.get("/customer-coupons", response_model=AdminCustomerCouponsResponse)
def admin_customer_coupons_list(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminCustomerCouponsResponse:
    return get_admin_customer_coupons(session)
