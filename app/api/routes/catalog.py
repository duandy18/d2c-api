from fastapi import APIRouter

from app.schemas.catalog import CatalogProductsResponse
from app.services.catalog_service import list_catalog_products

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
