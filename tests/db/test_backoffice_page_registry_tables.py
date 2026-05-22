from sqlalchemy import inspect

from app.core.config import load_settings
from app.core.database import create_db_engine


def test_backoffice_page_registry_table_exists() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)
        assert "d2c_backoffice_pages" in inspector.get_table_names()
    finally:
        engine.dispose()


def test_backoffice_page_registry_columns_and_indexes_exist() -> None:
    engine = create_db_engine(load_settings())
    try:
        inspector = inspect(engine)

        columns = {column["name"] for column in inspector.get_columns("d2c_backoffice_pages")}
        indexes = {index["name"] for index in inspector.get_indexes("d2c_backoffice_pages")}
        unique_constraints = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("d2c_backoffice_pages")
        }

        assert {
            "id",
            "page_code",
            "parent_code",
            "level",
            "title",
            "route_path",
            "component_key",
            "icon",
            "sort_order",
            "is_enabled",
            "is_visible",
            "implementation_status",
            "data_status",
            "required_permission",
            "created_at",
            "updated_at",
        }.issubset(columns)

        assert "ix_d2c_backoffice_pages_parent_code" in indexes
        assert "ix_d2c_backoffice_pages_route_path" in indexes
        assert "ix_d2c_backoffice_pages_sort_order" in indexes
        assert "uq_d2c_backoffice_pages_page_code" in unique_constraints
    finally:
        engine.dispose()
