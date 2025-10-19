import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.auth import User
from src.core.security import get_password_hash
from src.core.logging import logger


class InitialDataService:
    """Сервис для инициализации начальных данных"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_test_users(self):
        """Создание тестовых пользователей если их нет"""
        test_users = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "password": "admin123",
                "first_name": "Admin",
                "last_name": "User",
                "is_superuser": True,
                "is_active": True
            },
            {
                "email": "user@example.com",
                "username": "testuser",
                "password": "user123",
                "first_name": "Test",
                "last_name": "User",
                "is_superuser": False,
                "is_active": True
            },
            {
                "email": "operator@example.com",
                "username": "operator",
                "password": "operator123",
                "first_name": "Operator",
                "last_name": "User",
                "is_superuser": False,
                "is_active": True
            }
        ]

        created_count = 0
        for user_data in test_users:
            try:
                # Проверяем существование пользователя
                existing_user = await self.db.execute(
                    select(User).where(
                        (User.email == user_data["email"]) |
                        (User.username == user_data["username"])
                    )
                )
                existing_user = existing_user.scalar_one_or_none()

                if not existing_user:
                    # Создаем нового пользователя
                    user_dict = user_data.copy()
                    user_dict["hashed_password"] = get_password_hash(user_data["password"])
                    user_dict["id"] = uuid.uuid4()  # Генерируем UUID
                    del user_dict["password"]

                    user = User(**user_dict)
                    self.db.add(user)
                    await self.db.commit()
                    await self.db.refresh(user)

                    created_count += 1
                    logger.info(f"Создан тестовый пользователь: {user_data['email']}")
                else:
                    logger.debug(f"Пользователь уже существует: {user_data['email']}")

            except Exception as e:
                await self.db.rollback()
                logger.error(f"Ошибка создания пользователя {user_data['email']}: {e}")

        return created_count

    async def initialize_all(self):
        """Инициализация всех тестовых данных"""
        logger.info("Начало инициализации тестовых данных...")

        users_created = await self.create_test_users()

        logger.info(f"Инициализация завершена. Создано пользователей: {users_created}")
        return {
            "users_created": users_created
        }