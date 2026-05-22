from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import D2CSettings, load_settings


def create_db_engine(settings: D2CSettings | None = None) -> Engine:
    resolved_settings = settings or load_settings()
    return create_engine(resolved_settings.database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def iter_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
