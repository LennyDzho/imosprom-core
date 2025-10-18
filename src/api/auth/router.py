from dishka import FromDishka
from fastapi import APIRouter, HTTPException, status, Depends
from dishka.integrations.fastapi import DishkaRoute

from src.api.services.auth import AuthService
from src.core.infra.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from src.core.infra.exceptions import (
    UserAlreadyExists, InvalidCredentials, InvalidToken, UserNotFound
)

router = APIRouter(route_class=DishkaRoute, prefix="/auth", tags=["Аутентификация"])


@router.post("/register", summary="Регистрация пользователя", response_model=UserResponse)
async def register(
        user_data: UserCreate,
        service: FromDishka[AuthService],
):
    """
    Регистрация нового пользователя в системе.
    """
    try:
        success, error, user = await service.register_user(user_data)

        if success:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

    except UserAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/login", summary="Вход в систему", response_model=TokenResponse)
async def login(
        login_data: UserLogin,
        service: FromDishka[AuthService],
):
    """
    Аутентификация пользователя и выдача токенов.
    """
    try:
        tokens = await service.login_user(login_data)

        if tokens:
            return tokens
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or user inactive"
            )

    except InvalidCredentials as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/refresh", summary="Обновление токенов", response_model=TokenResponse)
async def refresh_tokens(
        refresh_token: str,
        service: FromDishka[AuthService],
):
    """
    Обновление access и refresh токенов.
    """
    try:
        tokens = await service.refresh_tokens(refresh_token)

        if tokens:
            return tokens
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/logout", summary="Выход из системы")
async def logout(
        access_token: str,
        service: FromDishka[AuthService],
):
    """
    Выход пользователя и инвалидация токенов.
    """
    try:
        success = await service.logout_user(access_token)

        if success:
            return {"message": "Successfully logged out"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token or already logged out"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/me", summary="Получить текущего пользователя", response_model=UserResponse)
async def get_current_user(
        access_token: str = Depends(),
        service: FromDishka[AuthService] = None,
):
    """
    Получение информации о текущем аутентифицированном пользователе.
    """
    try:
        user = await service.verify_token(access_token)

        if user:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

    except InvalidToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/verify", summary="Верификация токена")
async def verify_token(
        access_token: str,
        service: FromDishka[AuthService],
):
    """
    Проверка валидности access токена.
    """
    try:
        user = await service.verify_token(access_token)

        if user:
            return {
                "valid": True,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "is_superuser": user.is_superuser
                }
            }
        else:
            return {"valid": False}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )