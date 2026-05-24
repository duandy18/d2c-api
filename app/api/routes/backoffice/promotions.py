"""Backoffice promotion usage routes retained in d2c-api.

Promotion/coupon configuration owner APIs moved to d2c-backoffice-api.
d2c-api keeps customer coupon usage facts because checkout runtime still writes them.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.promotions.contracts.backoffice_promotion_contract import (
    BackofficeCustomerCouponsResponse,
)
from app.domains.promotions.services.backoffice_promotion_service import (
    get_backoffice_customer_coupons,
)

router = APIRouter(prefix="/backoffice/promotions", tags=["backoffice-promotions-usage"])
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


@router.get("/customer-coupons", response_model=BackofficeCustomerCouponsResponse)
def backoffice_customer_coupons_list(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeCustomerCouponsResponse:
    return get_backoffice_customer_coupons(session)
