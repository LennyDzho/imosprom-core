import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import EmailStr, Field, validator, BaseModel


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email пользователя")
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    first_name: Optional[str] = Field(None, max_length=100, description="Имя")
    last_name: Optional[str] = Field(None, max_length=100, description="Фамилия")

class UserCreate(UserBase):
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
    id: uuid.UUID = Field(..., description="UUID пользователя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    is_superuser: bool = Field(..., description="Является ли суперпользователем")
    created_at: datetime = Field(..., description="Дата создания")

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
    refresh_token: str = Field(..., description="Refresh token для обновления")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }

class LogoutRequest(BaseModel):
    access_token: str = Field(..., description="Access token для инвалидации")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }

class VerifyTokenRequest(BaseModel):
    access_token: str = Field(..., description="Access token для верификации")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }

class VerifyTokenResponse(BaseModel):
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

class AuthResponse(BaseModel):
    status: str = Field(..., description="Статус операции: success или error")
    message: str = Field(..., description="Сообщение о результате операции")
    user_id: Optional[uuid.UUID] = Field(None, description="ID пользователя (для успешной регистрации)")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")

    class Config:
        json_schema_extra = {
            "example_success": {
                "status": "success",
                "message": "User registered successfully",
                "user_id": "a1b2c3d4-1234-5678-9999-abcdefabcdef"
            },
            "example_error": {
                "status": "error",
                "message": "Email already registered"
            }
        }