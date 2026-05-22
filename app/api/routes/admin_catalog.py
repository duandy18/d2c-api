from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.admin_catalog import (
    AdminCatalogHealthResponse,
    AdminPriceListsResponse,
    AdminProductsResponse,
    AdminSkuPricesResponse,
    AdminSkusResponse,
    AdminUnitsResponse,
)
from app.services.admin_catalog_service import (
    get_admin_price_lists,
    get_admin_products,
    get_admin_sku_prices,
    get_admin_skus,
    get_admin_units,
)

router = APIRouter(prefix="/admin/catalog", tags=["admin-catalog"])
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


@router.get("/health", response_model=AdminCatalogHealthResponse)
def admin_catalog_health(_: AdminClientDep) -> AdminCatalogHealthResponse:
    return AdminCatalogHealthResponse(
        status="ok",
        module="admin_catalog",
        surface="merchant_read",
    )


@router.get("/units", response_model=AdminUnitsResponse)
def admin_catalog_units(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminUnitsResponse:
    return get_admin_units(session)


@router.get("/price-lists", response_model=AdminPriceListsResponse)
def admin_catalog_price_lists(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminPriceListsResponse:
    return get_admin_price_lists(session)


@router.get("/products", response_model=AdminProductsResponse)
def admin_catalog_products(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminProductsResponse:
    return get_admin_products(session)


@router.get("/skus", response_model=AdminSkusResponse)
def admin_catalog_skus(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminSkusResponse:
    return get_admin_skus(session)


@router.get("/sku-prices", response_model=AdminSkuPricesResponse)
def admin_catalog_sku_prices(
    _: AdminClientDep,
    session: SessionDep,
) -> AdminSkuPricesResponse:
    return get_admin_sku_prices(session)
