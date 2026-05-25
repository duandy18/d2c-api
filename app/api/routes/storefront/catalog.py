"""Storefront catalog routes; HTTP paths remain /catalog/*."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.domains.catalog.contracts.storefront_catalog_contract import (
    CatalogCategoriesResponse,
    CatalogProduct,
    CatalogProductsResponse,
)
from app.domains.catalog.services.storefront_catalog_service import (
    get_catalog_product,
    list_catalog_categories,
    list_catalog_products,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health")
def catalog_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "catalog",
        "data_source": "d2c_published_offer_snapshot",
    }


@router.get("/categories", response_model=CatalogCategoriesResponse)
def catalog_categories(session: SessionDep) -> CatalogCategoriesResponse:
    return list_catalog_categories(session)


@router.get("/products", response_model=CatalogProductsResponse)
def catalog_products(session: SessionDep) -> CatalogProductsResponse:
    return list_catalog_products(session)


@router.get("/products/{product_id}", response_model=CatalogProduct)
def catalog_product_detail(
    product_id: str,
    session: SessionDep,
) -> CatalogProduct:
    product = get_catalog_product(session, product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="catalog_product_not_found",
        )

    return product
