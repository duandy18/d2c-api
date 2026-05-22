from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import D2CSettings, load_settings


def create_app(settings: D2CSettings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()

    app = FastAPI(
        title="D2C API",
        version="0.1.0",
        description="D2C owned storefront API service.",
    )
    app.state.settings = resolved_settings
    app.include_router(api_router)

    return app


app = create_app()
