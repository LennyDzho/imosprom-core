from faststream import Context, Depends
from sqlalchemy.orm import Session
import uuid

from src.database.database import get_db
from src.database.models.auth import User


async def get_current_active_user(
        access_token: str = Context("message.headers.authorization", "").replace("Bearer ", ""),
        db: Session = Depends(get_db)
) -> User:
    """Получение текущего активного пользователя"""
    from src.api.services.auth import AuthService

    auth_service = AuthService(db)
    session = auth_service.session_repo.get_by_access_token(access_token)

    if not session or not session.user.is_active:
        raise ValueError("Invalid or expired token")

    return session.user


async def require_superuser(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """Проверка прав суперпользователя"""
    if not current_user.is_superuser:
        raise ValueError("Insufficient permissions")
    return current_user