import logging
from typing import AsyncGenerator

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.core.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 10,
        max_overflow: int = 10,
    ) -> None:
        self.engine: Engine = create_engine(
            url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

        self.async_engine: AsyncEngine = create_async_engine(
            url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )

        self.session_factory = async_sessionmaker(
            bind=self.async_engine, expire_on_commit=False, autoflush=False
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        logger.debug("Creating new database session...")
        async with self.session_factory() as session:
            yield session

    async def dispose(self) -> None:
        logger.info("Disposing database...")
        await self.async_engine.dispose()


db_helper: DatabaseHelper = DatabaseHelper(
    settings.db.connection_url(),
    echo=False,
    echo_pool=False,
    pool_size=10,
    max_overflow=50,
)
