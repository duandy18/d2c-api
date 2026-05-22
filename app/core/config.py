from __future__ import annotations

from dataclasses import dataclass
from os import getenv


def _read_csv_env(key: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = getenv(key)

    if raw_value is None:
        return fallback

    values = tuple(value.strip() for value in raw_value.split(",") if value.strip())

    if not values:
        return fallback

    return values


@dataclass(frozen=True)
class D2CSettings:
    environment: str = "local"
    app_code: str = "d2c"
    service_name: str = "d2c-api"
    service_client_code: str = "d2c-service"
    api_path: str = "/api/d2c"
    web_path: str = "/d2c"
    api_port: int = 8025
    database_url: str = "postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c"
    test_database_url: str = "postgresql+psycopg://d2c:d2c@127.0.0.1:5433/d2c_test"
    cors_allow_origins: tuple[str, ...] = (
        "http://127.0.0.1:5277",
        "http://localhost:5277",
        "http://127.0.0.1:5288",
        "http://localhost:5288",
    )


def load_settings() -> D2CSettings:
    return D2CSettings(
        environment=getenv("D2C_ENVIRONMENT", D2CSettings.environment),
        app_code=getenv("D2C_APP_CODE", D2CSettings.app_code),
        service_name=getenv("D2C_SERVICE_NAME", D2CSettings.service_name),
        service_client_code=getenv(
            "D2C_SERVICE_CLIENT_CODE",
            D2CSettings.service_client_code,
        ),
        api_path=getenv("D2C_API_PATH", D2CSettings.api_path),
        web_path=getenv("D2C_WEB_PATH", D2CSettings.web_path),
        api_port=int(getenv("D2C_API_PORT", str(D2CSettings.api_port))),
        database_url=getenv("D2C_DATABASE_URL", D2CSettings.database_url),
        test_database_url=getenv("D2C_TEST_DATABASE_URL", D2CSettings.test_database_url),
        cors_allow_origins=_read_csv_env(
            "D2C_CORS_ALLOW_ORIGINS",
            D2CSettings.cors_allow_origins,
        ),
    )
