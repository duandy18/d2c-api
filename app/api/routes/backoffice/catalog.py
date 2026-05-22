"""Backoffice catalog routes; HTTP paths are /backoffice/catalog/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.catalog.contracts.backoffice_catalog_contract import (
    BackofficeCatalogHealthResponse,
    BackofficePriceListsResponse,
    BackofficeProductsResponse,
    BackofficeSkuPricesResponse,
    BackofficeSkusResponse,
    BackofficeUnitsResponse,
)
from app.domains.catalog.services.backoffice_catalog_service import (
    get_backoffice_price_lists,
    get_backoffice_products,
    get_backoffice_sku_prices,
    get_backoffice_skus,
    get_backoffice_units,
)

router = APIRouter(prefix="/backoffice/catalog", tags=["backoffice-catalog"])
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


@router.get("/health", response_model=BackofficeCatalogHealthResponse)
def backoffice_catalog_health(_: BackofficeClientDep) -> BackofficeCatalogHealthResponse:
    return BackofficeCatalogHealthResponse(
        status="ok",
        module="backoffice_catalog",
        surface="merchant_read",
    )


@router.get("/units", response_model=BackofficeUnitsResponse)
def backoffice_catalog_units(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeUnitsResponse:
    return get_backoffice_units(session)


@router.get("/price-lists", response_model=BackofficePriceListsResponse)
def backoffice_catalog_price_lists(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficePriceListsResponse:
    return get_backoffice_price_lists(session)


@router.get("/products", response_model=BackofficeProductsResponse)
def backoffice_catalog_products(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeProductsResponse:
    return get_backoffice_products(session)


@router.get("/skus", response_model=BackofficeSkusResponse)
def backoffice_catalog_skus(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSkusResponse:
    return get_backoffice_skus(session)


@router.get("/sku-prices", response_model=BackofficeSkuPricesResponse)
def backoffice_catalog_sku_prices(
    _: BackofficeClientDep,
    session: SessionDep,
) -> BackofficeSkuPricesResponse:
    return get_backoffice_sku_prices(session)
