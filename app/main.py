from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()
