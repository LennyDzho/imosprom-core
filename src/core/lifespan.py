import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .initial_data import InitialDataService
from .taskiq_broker import broker
from ..database import db_helper

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup

    logger.info("Starting application....")

    # Инициализация тестовых данных
    try:
        logger.info("Инициализация тестовых данных...")
        async with db_helper.session_factory() as db:
            initial_data_service = InitialDataService(db)
            await initial_data_service.initialize_all()
    except Exception as e:
        logger.error(f"Ошибка инициализации тестовых данных: {e}")

    if not broker.is_worker_process:
        await broker.startup()
    yield
    if not broker.is_worker_process:
        await broker.shutdown()
    await db_helper.dispose()
    await app.state.dishka_container.close()

    logger.info("Application shutdown complete.")
