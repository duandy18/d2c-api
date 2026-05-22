from fastapi import FastAPI

APP_CODE = "d2c"
SERVICE_NAME = "d2c-api"
API_PATH = "/api/d2c"


def create_app() -> FastAPI:
    app = FastAPI(
        title="D2C API",
        version="0.1.0",
        description="D2C owned storefront API service.",
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app_code": APP_CODE,
            "service": SERVICE_NAME,
            "api_path": API_PATH,
        }

    return app


app = create_app()
