from fastapi import APIRouter

from app.api.routes.backoffice.promotions import router as backoffice_promotions_router
from app.api.routes.backoffice.site_config import router as backoffice_site_config_router
from app.api.routes.backoffice.support import router as backoffice_support_router
from app.api.routes.backoffice.support_live import router as backoffice_support_live_router
from app.api.routes.storefront.analytics import router as storefront_analytics_router
from app.api.routes.storefront.cart import router as storefront_cart_router
from app.api.routes.storefront.catalog import router as storefront_catalog_router
from app.api.routes.storefront.customers import router as storefront_customers_router
from app.api.routes.storefront.home import router as storefront_home_router
from app.api.routes.storefront.orders import router as storefront_orders_router
from app.api.routes.storefront.pages import router as storefront_pages_router
from app.api.routes.storefront.published import router as storefront_published_router
from app.api.routes.storefront.support import router as storefront_support_router
from app.api.routes.storefront.support_live import router as storefront_support_live_router
from app.api.routes.system.health import router as system_health_router

api_router = APIRouter()
api_router.include_router(backoffice_promotions_router)
api_router.include_router(backoffice_site_config_router)
api_router.include_router(backoffice_support_router)
api_router.include_router(backoffice_support_live_router)
api_router.include_router(storefront_analytics_router)
api_router.include_router(system_health_router)
api_router.include_router(storefront_cart_router)
api_router.include_router(storefront_catalog_router)
api_router.include_router(storefront_customers_router)
api_router.include_router(storefront_home_router)
api_router.include_router(storefront_pages_router)
api_router.include_router(storefront_orders_router)
api_router.include_router(storefront_support_router)
api_router.include_router(storefront_support_live_router)
api_router.include_router(storefront_published_router)
