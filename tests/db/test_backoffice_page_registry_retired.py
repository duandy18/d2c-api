from __future__ import annotations

from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_backoffice_page_registry_table_is_retired() -> None:
    engine = create_db_engine(load_settings())

    with engine.connect() as connection:
        inspector = inspect(connection)
        assert "d2c_backoffice_pages" not in inspector.get_table_names()
