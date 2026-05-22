from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import D2CSettings, load_settings


def create_db_engine(settings: D2CSettings | None = None) -> Engine:
    resolved_settings = settings or load_settings()
    return create_engine(resolved_settings.database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@lru_cache
def get_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory(database_url: str) -> sessionmaker[Session]:
    return create_session_factory(get_engine(database_url))


def get_session() -> Generator[Session, None, None]:
    settings = load_settings()
    session_factory = get_session_factory(settings.database_url)
    session = session_factory()

    try:
        yield session
    finally:
        session.close()


def iter_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()

    try:
        yield session
    finally:
        session.close()
