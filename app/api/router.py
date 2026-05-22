from fastapi import APIRouter

from app.api.routes.admin_catalog import router as admin_catalog_router
from app.api.routes.admin_promotions import router as admin_promotions_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.cart import router as cart_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.customers import router as customers_router
from app.api.routes.health import router as health_router
from app.api.routes.orders import router as orders_router

api_router = APIRouter()
api_router.include_router(admin_catalog_router)
api_router.include_router(admin_promotions_router)
api_router.include_router(analytics_router)
api_router.include_router(health_router)
api_router.include_router(cart_router)
api_router.include_router(catalog_router)
api_router.include_router(customers_router)
api_router.include_router(orders_router)
