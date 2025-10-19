import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from starlette.responses import RedirectResponse

from src.api import setup_container, api_router
from src.api.exception_handlers import not_api_key_exception_handler, invalid_api_key_exception_handler, \
    http_exception_handler, forbidden_exception_handler, \
    inactive_user_exception_handler, not_found_exception_handler, conflict_exception_handler
from src.core import setup_logging, settings
from src.core.infra.exceptions import NotApiKey, InvalidApiKey, Forbidden, InactiveUser, \
    NotFound, Conflict

from src.core.safe_init import initialize_test_users_safe

logger = logging.getLogger(__name__)

setup_logging(settings.app.debug)


@asynccontextmanager
async def custom_lifespan(app: FastAPI):
    """Кастомный lifespan с безопасной инициализацией тестовых данных"""
    # Startup
    logger.info("Запуск приложения...")

    # Инициализация тестовых данных (безопасно, без моделей)
    await initialize_test_users_safe()

    yield

    # Shutdown
    logger.info("Остановка приложения...")


app = FastAPI(
    debug=settings.app.debug,
    lifespan=custom_lifespan,  # Используем наш кастомный lifespan
    title="CT Screening API",
    version="0.1.0beta",
    docs_url="/swagger",
    redoc_url=None,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

setup_container(app)

# Обработчики исключений
app.add_exception_handler(NotApiKey, not_api_key_exception_handler)
app.add_exception_handler(InvalidApiKey, invalid_api_key_exception_handler)
app.add_exception_handler(NotFound, not_found_exception_handler)
app.add_exception_handler(Conflict, conflict_exception_handler)
app.add_exception_handler(Exception, http_exception_handler)

@app.get("/", include_in_schema=False)
async def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse("/docs")


@app.get("/docs", include_in_schema=False)
async def init_scalar_docs():
    return get_scalar_api_reference(
        title=app.title,
        openapi_url=app.openapi_url,
        hide_models=True,
        hide_download_button=True,
    )


# Эндпоинт для отладки - проверка пользователей
@app.get("/debug/users", tags=["debug"])
async def debug_users():
    """Эндпоинт для отладки - показать всех пользователей"""
    try:
        from sqlalchemy import text
        from src.database.helper import db_helper

        async with db_helper.session_factory() as session:
            result = await session.execute(
                text("SELECT id, email, username, first_name, last_name, is_active, is_superuser FROM users")
            )
            users = result.fetchall()
            return {
                "total": len(users),
                "users": [
                    {
                        "id": str(user[0]),
                        "email": user[1],
                        "username": user[2],
                        "first_name": user[3],
                        "last_name": user[4],
                        "is_active": user[5],
                        "is_superuser": user[6]
                    }
                    for user in users
                ]
            }
    except Exception as e:
        return {"error": str(e)}


# Эндпоинт для проверки статуса инициализации
@app.get("/debug/init-status", tags=["debug"])
async def debug_init_status():
    """Проверка статуса инициализации тестовых данных"""
    try:
        from sqlalchemy import text
        from src.database.helper import db_helper

        async with db_helper.session_factory() as session:
            # Проверяем количество пользователей
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()

            # Проверяем существование тестовых пользователей
            test_emails = ["admin@example.com", "user@example.com", "operator@example.com"]
            existing_test_users = []

            for email in test_emails:
                result = await session.execute(
                    text("SELECT username FROM users WHERE email = :email"),
                    {"email": email}
                )
                user = result.first()
                if user:
                    existing_test_users.append({"email": email, "username": user[0]})

            return {
                "total_users": user_count,
                "test_users_created": len(existing_test_users),
                "test_users": existing_test_users,
                "status": "initialized" if len(existing_test_users) > 0 else "not_initialized"
            }
    except Exception as e:
        return {"error": str(e), "status": "error"}


app.include_router(api_router)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except (KeyboardInterrupt, SystemExit):
        pass