from fastapi import FastAPI

from app.core.config import D2CSettings, load_settings


def create_app(settings: D2CSettings | None = None) -> FastAPI:
    resolved_settings = settings or load_settings()

    app = FastAPI(
        title="D2C API",
        version="0.1.0",
        description="D2C owned storefront API service.",
    )
    app.state.settings = resolved_settings

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": resolved_settings.environment,
            "app_code": resolved_settings.app_code,
            "service": resolved_settings.service_name,
            "api_path": resolved_settings.api_path,
        }

    return app


app = create_app()
