# Реализация системы авторизации и инициализации тестовых данных

## Обзор

Реализована полная система аутентификации и авторизации с автоматической инициализацией тестовых пользователей при запуске приложения. Система включает регистрацию, вход, управление токенами и защиту эндпоинтов.

## Реализованные эндпоинты

### ✅ 1. Регистрация пользователя

**Метод:** `POST /auth/register`

**Файлы:**
- `src/api/routers/auth.py` - обработчик `register()`
- `src/api/services/auth.py` - метод `register_user()`
- `src/core/infra/schemas.py` - схема `UserCreate`

**Функциональность:**
- Создание нового пользователя в системе
- Проверка уникальности email и username
- Хэширование пароля перед сохранением
- Валидация входных данных

**Пример запроса:**
```json
{
  "email": "user@example.com",
  "username": "newuser",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

### ✅ 2. Вход в систему

**Метод:** `POST /auth/login`

**Файлы:**
- `src/api/routers/auth.py` - обработчик `login()`
- `src/api/services/auth.py` - метод `login_user()`
- `src/core/infra/schemas.py` - схема `UserLogin`

**Функциональность:**
- Аутентификация пользователя по email/username и паролю
- Генерация access и refresh токенов
- Создание пользовательской сессии
- Возврат данных пользователя и токенов

**Пример запроса:**
```json
{
  "email": "admin@example.com",
  "password": "admin123"
}
```

### ✅ 3. Обновление токенов

**Метод:** `POST /auth/refresh`

**Файлы:**
- `src/api/routers/auth.py` - обработчик `refresh_tokens()`
- `src/api/services/auth.py` - метод `refresh_tokens()`
- `src/core/infra/schemas.py` - схема `RefreshTokenRequest`

**Функциональность:**
- Обновление access и refresh токенов
- Валидация refresh токена
- Создание новой сессии
- Инвалидация старой сессии

**Пример запроса:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### ✅ 4. Выход из системы

**Метод:** `POST /auth/logout`

**Файлы:**
- `src/api/routers/auth.py` - обработчик `logout()`
- `src/api/services/auth.py` - метод `logout_user()`
- `src/core/infra/schemas.py` - схема `LogoutRequest`

**Функциональность:**
- Инвалидация текущей сессии пользователя
- Удаление access токена из активных сессий
- Завершение всех сессий пользователя

**Пример запроса:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### ✅ 5. Получение текущего пользователя

**Метод:** `GET /auth/me`

**Файлы:**
- `src/api/routers/auth.py` - обработчик `get_current_user()`
- `src/api/services/auth.py` - метод `verify_token()`
- `src/core/infra/schemas.py` - схема `UserResponse`

**Функциональность:**
- Получение данных текущего аутентифицированного пользователя
- Верификация access токена
- Проверка активности пользователя

### ✅ 6. Верификация токена

**Метод:** `POST /auth/verify`

**Файлы:**
- `src/api/routers/auth.py` - обработчик `verify_token()`
- `src/api/services/auth.py` - метод `verify_token()`
- `src/core/infra/schemas.py` - схема `VerifyTokenRequest`

**Функциональность:**
- Проверка валидности access токена
- Возврат информации о пользователе при успешной верификации

**Пример запроса:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Архитектура

### Структура файлов

```
src/
├── api/
│   ├── auth/
│   │   └── router.py              # Эндпоинты аутентификации
│   └── services/
│       └── auth.py              # Бизнес-логика аутентификации
├── core/
│   ├── safe_init.py             # Безопасная инициализация данных
│   ├── security.py              # Хэширование паролей
│   └── infra/
│       └── schemas.py           # Схемы запросов/ответов
├── database/
│   ├── models/
│   │   └── auth.py              # Модели пользователей и сессий
│   └── repositories/
│       └── auth.py              # Репозитории для работы с БД
└── guard/
    └── auth.py                  # Guard для защиты эндпоинтов
```

### Интеграция

1. **Роутер** (`auth.py`) - обработка HTTP запросов аутентификации
2. **Сервис** (`auth.py`) - бизнес-логика регистрации, входа, управления токенами
3. **Репозитории** - работа с базой данных пользователей и сессий
4. **Guard** (`auth_guard`) - защита API эндпоинтов
5. **Safe Init** - автоматическая инициализация тестовых данных

### Dependency Injection

- `AuthProvider` - предоставляет сервисы аутентификации
- `DatabaseProvider` - управление сессиями БД
- `InitDataProvider` - инициализация тестовых данных
- Интегрировано в главный контейнер в `src/core/init/__init__.py`

## Автоматическая инициализация тестовых данных

### Функциональность

- Автоматическое создание тестовых пользователей при запуске приложения
- Проверка существования пользователей перед созданием
- Безопасное хэширование паролей
- Поддержка разных ролей пользователей

### Тестовые пользователи

**👑 Администратор:**
- Email: `admin@example.com`
- Пароль: `admin123`
- Права: суперпользователь

**👤 Обычный пользователь:**
- Email: `user@example.com`
- Пароль: `user123`
- Права: базовые

**🛠️ Оператор:**
- Email: `operator@example.com`
- Пароль: `operator123`
- Права: операторские

### Решение проблем циклических зависимостей

**Проблема:** Ошибка инициализации SQLAlchemy моделей из-за циклических ссылок

**Решение:** Использование прямого SQL подхода в `safe_init.py`
- Обход загрузки моделей SQLAlchemy
- Прямые SQL запросы для создания пользователей
- Изоляция от проблемных зависимостей

## База данных

### Структура таблиц

```sql
-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Таблица сессий пользователей
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_token VARCHAR(512) UNIQUE NOT NULL,
    refresh_token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);
```

## Эндпоинты для отладки

### 📊 Проверка статуса инициализации

**Метод:** `GET /debug/init-status`

**Функциональность:**
- Проверка количества пользователей в системе
- Подтверждение создания тестовых пользователей
- Статус инициализации системы

**Пример ответа:**
```json
{
  "total_users": 3,
  "test_users_created": 3,
  "test_users": [
    {"email": "admin@example.com", "username": "admin"},
    {"email": "user@example.com", "username": "testuser"},
    {"email": "operator@example.com", "username": "operator"}
  ],
  "status": "initialized"
}
```

### 👥 Просмотр всех пользователей

**Метод:** `GET /debug/users`

**Функциональность:**
- Получение списка всех пользователей системы
- Информация о правах и статусе пользователей
- Отладка процесса аутентификации

**Пример ответа:**
```json
{
  "total": 3,
  "users": [
    {
      "id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
      "email": "admin@example.com",
      "username": "admin",
      "first_name": "Admin",
      "last_name": "User",
      "is_active": true,
      "is_superuser": true
    }
  ]
}
```

## Использование

### Запуск приложения

```bash
# Запуск через Python
poetry run python src/run/main.py

# Или через Uvicorn
poetry run uvicorn src.run.main:app --host 0.0.0.0 --port 8000 --reload
```

### Настройка переменных окружения

```env
# База данных PostgreSQL
DB_NAME=agent_core
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432

# JWT настройки
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenRouter (для LLM функциональности)
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

### Примеры использования

#### Регистрация нового пользователя
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "username": "newuser",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Вход в систему
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123"
  }'
```

#### Получение данных текущего пользователя
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Проверка статуса инициализации
```bash
curl -X GET "http://localhost:8000/debug/init-status"
```

## Мониторинг и логи

### Логи инициализации

При успешном запуске в логах отображается:

```
🚀 Запуск приложения...
🧪 Безопасная инициализация тестовых пользователей...
✅ Таблица users существует
✅ Создан пользователь: admin@example.com
✅ Создан пользователь: user@example.com
✅ Создан пользователь: operator@example.com
🎉 Инициализация завершена. Создано пользователей: 3
```

### Обработка ошибок

- Детальное логирование ошибок инициализации
- Graceful degradation при проблемах с БД
- Корректная работа приложения даже при ошибках инициализации

## Безопасность

- Хэширование паролей с использованием соли
- JWT токены с настраиваемым временем жизни
- Валидация всех входных данных через Pydantic
- Защита от SQL-инъекций через параметризованные запросы
- Проверка прав доступа к защищенным эндпоинтам

## Производительность

- Асинхронные операции с базой данных
- Connection pooling для PostgreSQL
- Эффективные SQL запросы
- Минимальные накладные расходы при инициализации

Система готова к использованию и обеспечивает надежную основу для аутентификации пользователей с автоматической инициализацией тестовых данных.