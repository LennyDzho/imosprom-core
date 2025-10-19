from fastapi import FastAPI
from src.core.initial_data import InitialDataService
from src.core.logging import logger


async def create_start_app_handler(app: FastAPI):
    """Обработчик запуска приложения"""

    async def start_app() -> None:
        logger.info("Инициализация тестовых данных...")

        try:
            # Получаем сервис из состояния приложения или создаем новый
            db = app.state.db_session  # Предполагается, что сессия БД в состоянии app
            initial_data_service = InitialDataService(db)
            await initial_data_service.initialize_all()
        except Exception as e:
            logger.error(f"Ошибка инициализации тестовых данных: {e}")

    return start_app


def setup_events(app: FastAPI):
    """Настройка событий приложения"""
    app.add_event_handler("startup", create_start_app_handler(app))