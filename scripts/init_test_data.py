import asyncio
import asyncpg
import hashlib
import secrets
import uuid
import os


def get_password_hash(password: str) -> str:
    """Упрощенное хэширование пароля"""
    salt = secrets.token_hex(16)
    return f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"


async def init_database():
    """Прямое подключение к базе данных"""
    print("🔐 Прямая инициализация тестовых данных в PostgreSQL...")

    # Параметры подключения (замените на ваши)
    DB_CONFIG = {
        "database": "agent_core",
        "user": "postgres",
        "password": "123456",
        "host": "localhost",
        "port": 5432
    }

    try:
        # Подключаемся к базе
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ Подключение к PostgreSQL установлено")

        # Проверяем существование таблицы users
        try:
            await conn.execute("SELECT 1 FROM users LIMIT 1")
            print("✅ Таблица users существует")
        except:
            print("❌ Таблица users не существует")
            print("💡 Сначала выполните SQL скрипт создания таблиц")
            await conn.close()
            return 1

        # Тестовые пользователи
        test_users = [
            {
                "email": "admin@example.com",
                "username": "admin",
                "password": "admin123",
                "first_name": "Admin",
                "last_name": "User",
                "is_superuser": True
            },
            {
                "email": "user@example.com",
                "username": "testuser",
                "password": "user123",
                "first_name": "Test",
                "last_name": "User",
                "is_superuser": False
            },
            {
                "email": "operator@example.com",
                "username": "operator",
                "password": "operator123",
                "first_name": "Operator",
                "last_name": "User",
                "is_superuser": False
            }
        ]

        created_count = 0

        for user_data in test_users:
            try:
                # Проверяем существование пользователя
                existing = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1 OR username = $2",
                    user_data["email"], user_data["username"]
                )

                if not existing:
                    # Создаем пользователя
                    user_id = uuid.uuid4()
                    hashed_password = get_password_hash(user_data["password"])

                    await conn.execute('''
                        INSERT INTO users (id, email, username, hashed_password, first_name, last_name, is_superuser, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, true)
                    ''', user_id, user_data["email"], user_data["username"], hashed_password,
                                       user_data["first_name"], user_data["last_name"], user_data["is_superuser"])

                    created_count += 1
                    print(f"✅ Создан пользователь: {user_data['email']}")
                else:
                    print(f"⚠️  Пользователь уже существует: {user_data['email']}")

            except Exception as e:
                print(f"❌ Ошибка создания пользователя {user_data['email']}: {e}")

        await conn.close()

        print(f"\n🎉 Инициализация завершена!")
        print(f"📊 Создано пользователей: {created_count}")

        if created_count > 0:
            print("\n📋 Тестовые пользователи:")
            for user in test_users:
                print(f"   📧 {user['email']} / {user['password']}")

        return 0

    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return 1


async def main():
    return await init_database()


if __name__ == "__main__":
    exit(asyncio.run(main()))