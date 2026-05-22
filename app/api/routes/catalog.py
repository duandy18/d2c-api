from fastapi import APIRouter, HTTPException, status

from app.schemas.catalog import CatalogProduct, CatalogProductsResponse
from app.services.catalog_service import get_catalog_product, list_catalog_products

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/health")
def catalog_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "catalog",
        "data_source": "placeholder_static_catalog",
        "future_source": "pms_projection",
    }


@router.get("/products", response_model=CatalogProductsResponse)
def catalog_products() -> CatalogProductsResponse:
    return list_catalog_products()


@router.get("/products/{product_id}", response_model=CatalogProduct)
def catalog_product_detail(product_id: str) -> CatalogProduct:
    product = get_catalog_product(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="catalog_product_not_found",
        )

    return product
