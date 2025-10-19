from typing import Optional, Tuple
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.models.auth import Operator
from src.database.repositories.auth import UserRepository, UserSessionRepository, OperatorRepository
from src.core.security import create_access_token, create_refresh_token, verify_token
from src.core.config import settings
from src.api.schemas import UserCreate, UserLogin, TokenResponse


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = UserSessionRepository(db)

    def register_user(self, user_data: UserCreate) -> Tuple[bool, Optional[str]]:
        # Check if user already exists
        if self.user_repo.get_by_email(user_data.email):
            return False, "Email already registered"

        if self.user_repo.get_by_username(user_data.username):
            return False, "Username already taken"

        # Create user
        user_dict = user_data.model_dump()
        user = self.user_repo.create(user_dict)

        return True, None

    def login_user(self, login_data: UserLogin, ip_address: str = None, user_agent: str = None) -> Optional[
        TokenResponse]:
        # Authenticate user
        user = self.user_repo.authenticate(
            email=login_data.email,
            username=login_data.username,
            password=login_data.password
        )

        if not user:
            return None

        if not user.is_active:
            return None

        # Create tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

        # Create session
        session_data = {
            "user_id": user.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        self.session_repo.create(session_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )

    def refresh_tokens(self, refresh_token: str) -> Optional[TokenResponse]:
        # Verify refresh token
        payload = verify_token(refresh_token)
        if not payload:
            return None

        user_id = uuid.UUID(payload.get("sub"))
        user = self.user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            return None

        # Check if session exists and is valid
        session = self.session_repo.get_by_refresh_token(refresh_token)
        if not session:
            return None

        # Create new tokens
        new_access_token = create_access_token({"sub": str(user.id)})
        new_refresh_token = create_refresh_token({"sub": str(user.id)})

        # Update session
        session.access_token = new_access_token
        session.refresh_token = new_refresh_token
        session.expires_at = datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        session.last_activity = datetime.utcnow()

        self.db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )

    def logout_user(self, access_token: str) -> bool:
        session = self.session_repo.get_by_access_token(access_token)
        if session:
            self.session_repo.deactivate_session(session.id)
            return True
        return False

    def logout_all_sessions(self, user_id: uuid.UUID) -> None:
        self.session_repo.deactivate_all_user_sessions(user_id)


class OperatorService:
    def __init__(self, db: Session):
        self.db = db
        self.operator_repo = OperatorRepository(db)
        self.user_repo = UserRepository(db)

    def create_operator_profile(self, user_id: uuid.UUID, operator_data: OperatorCreate) -> Optional[Operator]:
        # Check if user exists
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None

        # Check if operator profile already exists
        existing_operator = self.operator_repo.get_by_user_id(user_id)
        if existing_operator:
            return None

        # Create operator profile
        operator_dict = operator_data.model_dump()
        operator_dict["user_id"] = user_id

        return self.operator_repo.create(operator_dict)

    def get_least_loaded_operator(self) -> Optional[Operator]:
        available_operators = self.operator_repo.get_available_operators()
        if not available_operators:
            return None

        # Return operator with lowest current load
        return min(available_operators, key=lambda op: op.current_load)