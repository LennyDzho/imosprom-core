import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, validator, EmailStr

from src.core.infra.enums import ErrorStatus


class BaseApiResponse(BaseModel):
    status: str = Field(default="ok", examples=["ok", "error"])
    message: str


class ErrorData(BaseModel):
    code: int
    message: str
    status: ErrorStatus


class ErrorResponse(BaseModel):
    error: ErrorData

class UserBase(BaseModel):
    """
    Базовая модель пользователя
    """
    email: EmailStr = Field(..., description="Email пользователя")
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    first_name: Optional[str] = Field(None, max_length=100, description="Имя")
    last_name: Optional[str] = Field(None, max_length=100, description="Фамилия")


class UserCreate(UserBase):
    """
    Модель для регистрации пользователя
    """
    password: str = Field(..., min_length=8, max_length=100, description="Пароль")

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "securepassword123",
                "first_name": "John",
                "last_name": "Doe"
            }
        }


class UserLogin(BaseModel):
    """
    Модель для входа пользователя
    """
    email: Optional[EmailStr] = Field(None, description="Email пользователя")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., description="Пароль")

    @validator('*', pre=True)
    def check_credentials(cls, v, values, **kwargs):
        if 'email' not in values and 'username' not in values:
            raise ValueError('Either email or username must be provided')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class UserResponse(UserBase):
    """
    Модель ответа с данными пользователя
    """
    id: uuid.UUID = Field(..., description="UUID пользователя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    is_superuser: bool = Field(..., description="Является ли суперпользователем")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
                "email": "user@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T12:00:00Z"
            }
        }


class TokenResponse(BaseModel):
    """
    Модель ответа с токенами авторизации
    """
    access_token: str = Field(..., description="Access token для авторизации")
    refresh_token: str = Field(..., description="Refresh token для обновления access token")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(..., description="Время жизни access token в секундах")
    user: UserResponse = Field(..., description="Данные пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True,
                    "is_superuser": False,
                    "created_at": "2024-01-01T12:00:00Z"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Модель запроса для обновления токенов
    """
    refresh_token: str = Field(..., description="Refresh token для обновления")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class LogoutRequest(BaseModel):
    """
    Модель запроса для выхода из системы
    """
    access_token: str = Field(..., description="Access token для инвалидации")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class VerifyTokenRequest(BaseModel):
    """
    Модель запроса для верификации токена
    """
    access_token: str = Field(..., description="Access token для верификации")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class VerifyTokenResponse(BaseModel):
    """
    Модель ответа верификации токена
    """
    valid: bool = Field(..., description="Валиден ли токен")
    user: Optional[Dict[str, Any]] = Field(None, description="Данные пользователя, если токен валиден")

    class Config:
        json_schema_extra = {
            "example_valid": {
                "valid": True,
                "user": {
                    "id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
                    "email": "user@example.com",
                    "username": "johndoe",
                    "is_superuser": False
                }
            },
            "example_invalid": {
                "valid": False
            }
        }


class ErrorResponse(BaseModel):
    """
    Модель ответа с ошибкой
    """
    detail: str = Field(..., description="Сообщение об ошибке")
    error_code: Optional[str] = Field(None, description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "User already exists",
                "error_code": "USER_ALREADY_EXISTS"
            }
        }


class SuccessResponse(BaseModel):
    """
    Модель успешного ответа
    """
    message: str = Field(..., description="Сообщение об успехе")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "data": {"user_id": "a1b2c3d4-1234-5678-9999-abcdefabcdef"}
            }
        }


# AI и RAG схемы

class Citation(BaseModel):
    """
    Модель цитаты из базы знаний
    """
    id: str = Field(..., description="ID цитаты")
    title: str = Field(..., description="Заголовок источника")
    url: Optional[str] = Field(None, description="URL источника")
    score: float = Field(..., description="Релевантность цитаты")


class AgentMessage(BaseModel):
    """
    Модель сообщения для агента
    """
    text: str = Field(..., description="Текст сообщения")
    lang: str = Field(default="ru", description="Язык сообщения")


class AgentContext(BaseModel):
    """
    Модель контекста для агента
    """
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="История диалога")
    kb_filters: Optional[Dict[str, Any]] = Field(default={}, description="Фильтры для базы знаний")


class AgentRequest(BaseModel):
    """
    Модель запроса к агенту
    """
    dialog_id: uuid.UUID = Field(..., description="ID диалога")
    task_id: uuid.UUID = Field(..., description="ID задачи")
    trace_id: uuid.UUID = Field(..., description="ID для трассировки")
    model: Optional[str] = Field(None, description="Модель для использования")
    message: AgentMessage = Field(..., description="Сообщение пользователя")
    context: AgentContext = Field(..., description="Контекст диалога")

    class Config:
        json_schema_extra = {
            "example": {
                "dialog_id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
                "task_id": "b2c3d4e5-2345-6789-0000-bcdefabcdefa",
                "trace_id": "c3d4e5f6-3456-7890-1111-cdefabcdefab",
                "model": "google/gemini-2.0-flash-exp:free",
                "message": {
                    "text": "Как восстановить пароль?",
                    "lang": "ru"
                },
                "context": {
                    "history": [{"role": "user", "text": "Привет"}],
                    "kb_filters": {"product": "AppX", "version": "1.2"}
                }
            }
        }


class AgentReply(BaseModel):
    """
    Модель ответа агента
    """
    text: str = Field(..., description="Текст ответа")
    citations: List[Citation] = Field(default=[], description="Цитаты из базы знаний")


class AgentResponse(BaseModel):
    """
    Модель ответа от агента
    """
    dialog_id: uuid.UUID = Field(..., description="ID диалога")
    task_id: uuid.UUID = Field(..., description="ID задачи")
    trace_id: uuid.UUID = Field(..., description="ID для трассировки")
    model: str = Field(..., description="Использованная модель")
    action: str = Field(..., description="Действие: auto|clarify|escalate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность ответа")
    reply: AgentReply = Field(..., description="Ответ агента")

    class Config:
        json_schema_extra = {
            "example": {
                "dialog_id": "a1b2c3d4-1234-5678-9999-abcdefabcdef",
                "task_id": "b2c3d4e5-2345-6789-0000-bcdefabcdefa",
                "trace_id": "c3d4e5f6-3456-7890-1111-cdefabcdefab",
                "model": "google/gemini-2.0-flash-exp:free",
                "action": "auto",
                "confidence": 0.82,
                "reply": {
                    "text": "Чтобы восстановить пароль, перейдите в настройки аккаунта и выберите пункт 'Сброс пароля'.",
                    "citations": [
                        {
                            "id": "KB-123",
                            "title": "Сброс пароля",
                            "url": "https://kb/appx/reset-password",
                            "score": 0.95
                        }
                    ]
                }
            }
        }


# Схемы для обновления базы знаний

class KnowledgeDocument(BaseModel):
    """
    Модель документа базы знаний
    """
    title: str = Field(..., description="Заголовок документа")
    content: str = Field(..., description="Содержимое документа")
    tags: Optional[List[str]] = Field(default=[], description="Теги документа")
    product: Optional[str] = Field(None, description="Продукт")
    version: Optional[str] = Field(None, description="Версия")


class KnowledgeUpdateRequest(BaseModel):
    """
    Модель запроса на обновление базы знаний
    """
    document_id: uuid.UUID = Field(..., description="ID документа")
    action: str = Field(..., description="Действие: add|update|delete")
    document: Optional[KnowledgeDocument] = Field(None, description="Документ")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "d4e5f6g7-4567-8901-2222-defabcdefabc",
                "action": "add",
                "document": {
                    "title": "Восстановление пароля",
                    "content": "Для восстановления пароля перейдите в раздел Настройки...",
                    "tags": ["пароль", "безопасность"],
                    "product": "AppX",
                    "version": "1.2"
                }
            }
        }