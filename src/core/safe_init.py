# src/core/safe_init.py
import logging
import uuid
import hashlib
import secrets
from sqlalchemy import text
from src.database.helper import db_helper

logger = logging.getLogger(__name__)


def get_password_hash(password: str) -> str:
    """Упрощенное хэширование пароля"""
    salt = secrets.token_hex(16)
    return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"


async def initialize_test_users_safe():
    """Безопасная инициализация тестовых пользователей без загрузки моделей"""
    logger.info("🧪 Безопасная инициализация тестовых пользователей...")

    try:
        test_users = [
            {
                "id": str(uuid.uuid4()),
                "email": "admin@example.com",
                "username": "admin",
                "hashed_password": get_password_hash("admin123"),
                "first_name": "Admin",
                "last_name": "User",
                "is_superuser": True,
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "email": "user@example.com",
                "username": "testuser",
                "hashed_password": get_password_hash("user123"),
                "first_name": "Test",
                "last_name": "User",
                "is_superuser": False,
                "is_active": True
            },
            {
                "id": str(uuid.uuid4()),
                "email": "operator@example.com",
                "username": "operator",
                "hashed_password": get_password_hash("operator123"),
                "first_name": "Operator",
                "last_name": "User",
                "is_superuser": False,
                "is_active": True
            }
        ]

        created_count = 0

        async with db_helper.session_factory() as session:
            # Проверяем существование таблицы users
            try:
                await session.execute(text("SELECT 1 FROM users LIMIT 1"))
                logger.info("✅ Таблица users существует")
            except Exception as e:
                logger.error(f"❌ Таблица users не существует: {e}")
                logger.info("💡 Сначала выполните SQL скрипт создания таблиц")
                return created_count

            # Создаем пользователей через прямой SQL
            for user_data in test_users:
                try:
                    # Проверяем существование пользователя
                    result = await session.execute(
                        text("SELECT id FROM users WHERE email = :email OR username = :username"),
                        {"email": user_data["email"], "username": user_data["username"]}
                    )
                    existing_user = result.first()

                    if not existing_user:
                        # Создаем нового пользователя
                        await session.execute(
                            text("""
                                INSERT INTO users (id, email, username, hashed_password, first_name, last_name, is_superuser, is_active)
                                VALUES (:id, :email, :username, :hashed_password, :first_name, :last_name, :is_superuser, :is_active)
                            """),
                            user_data
                        )
                        await session.commit()
                        created_count += 1
                        logger.info(f"✅ Создан пользователь: {user_data['email']}")
                    else:
                        logger.debug(f"⚠️ Пользователь уже существует: {user_data['email']}")

                except Exception as e:
                    await session.rollback()
                    logger.error(f"❌ Ошибка создания пользователя {user_data['email']}: {e}")

        logger.info(f"🎉 Инициализация завершена. Создано пользователей: {created_count}")

        if created_count > 0:
            logger.info("📋 Тестовые пользователи:")
            logger.info("   👑 admin@example.com / admin123 (суперпользователь)")
            logger.info("   👤 user@example.com / user123")
            logger.info("   🛠️  operator@example.com / operator123")

        return created_count

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при инициализации пользователей: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0