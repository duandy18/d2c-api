"""Runtime published model inspection routes.

These routes are not the public storefront catalog. Storefront/cart/checkout
will switch to the published model in later cuts.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.published.contracts.published_contract import (
    PublishedCouponsResponse,
    PublishedHealthResponse,
    PublishedPricesResponse,
    PublishedProductsResponse,
    PublishedPromotionsResponse,
    PublishedSkusResponse,
    PublishSyncRunsResponse,
)
from app.domains.published.services.published_service import (
    get_publish_sync_runs,
    get_published_coupons,
    get_published_health,
    get_published_prices,
    get_published_products,
    get_published_promotions,
    get_published_skus,
)

router = APIRouter(prefix="/published", tags=["published"])
SessionDep = Annotated[Session, Depends(get_session)]


def require_service_client(
    x_service_client: Annotated[str | None, Header(alias="X-Service-Client")] = None,
) -> None:
    if x_service_client != "d2c-service":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="service_client_required",
        )


ServiceClientDep = Annotated[None, Depends(require_service_client)]


@router.get("/health", response_model=PublishedHealthResponse)
def published_health(_: ServiceClientDep) -> PublishedHealthResponse:
    return get_published_health()


@router.get("/products", response_model=PublishedProductsResponse)
def published_products(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishedProductsResponse:
    return get_published_products(session)


@router.get("/skus", response_model=PublishedSkusResponse)
def published_skus(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishedSkusResponse:
    return get_published_skus(session)


@router.get("/prices", response_model=PublishedPricesResponse)
def published_prices(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishedPricesResponse:
    return get_published_prices(session)


@router.get("/promotions", response_model=PublishedPromotionsResponse)
def published_promotions(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishedPromotionsResponse:
    return get_published_promotions(session)


@router.get("/coupons", response_model=PublishedCouponsResponse)
def published_coupons(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishedCouponsResponse:
    return get_published_coupons(session)


@router.get("/sync-runs", response_model=PublishSyncRunsResponse)
def published_sync_runs(
    _: ServiceClientDep,
    session: SessionDep,
) -> PublishSyncRunsResponse:
    return get_publish_sync_runs(session)
