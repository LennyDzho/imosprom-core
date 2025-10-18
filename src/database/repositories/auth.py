from typing import Optional, List
from sqlalchemy import select, and_, update
from sqlalchemy.orm import joinedload
import uuid
from datetime import datetime

from src.database.models.auth import User, UserSession, Operator
from src.database.repositories.base import BaseRepo


class UserRepository(BaseRepo):
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_sessions(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).options(joinedload(User.sessions)).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user_data: dict) -> User:
        hashed_password = get_password_hash(user_data.pop('password'))
        user = User(**user_data, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, email: Optional[str] = None, username: Optional[str] = None, password: str = None) -> \
    Optional[User]:
        if not (email or username):
            return None

        user = None
        if email:
            user = await self.get_by_email(email)
        elif username:
            user = await self.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            return None

        return user

    async def update_last_activity(self, user_id: uuid.UUID) -> None:
        stmt = update(User).where(User.id == user_id).values(updated_at=datetime.utcnow())
        await self.session.execute(stmt)
        await self.session.commit()


class UserSessionRepository(BaseRepo):
    async def get_by_id(self, session_id: uuid.UUID) -> Optional[UserSession]:
        stmt = select(UserSession).where(UserSession.id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_access_token(self, access_token: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(
            and_(
                UserSession.access_token == access_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_sessions(self, user_id: uuid.UUID) -> List[UserSession]:
        stmt = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).order_by(UserSession.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, session_data: dict) -> UserSession:
        session = UserSession(**session_data)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def deactivate_session(self, access_token: str) -> bool:
        session = await self.get_by_access_token(access_token)
        if session:
            session.is_active = False
            await self.session.commit()
            return True
        return False

    async def deactivate_session_by_id(self, session_id: uuid.UUID) -> bool:
        session = await self.get_by_id(session_id)
        if session:
            session.is_active = False
            await self.session.commit()
            return True
        return False

    async def deactivate_all_user_sessions(self, user_id: uuid.UUID) -> int:
        stmt = update(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).values(is_active=False)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def update_session_tokens(self, session_id: uuid.UUID, access_token: str, refresh_token: str,
                                    expires_at: datetime) -> bool:
        stmt = update(UserSession).where(UserSession.id == session_id).values(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            last_activity=datetime.utcnow()
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def update_last_activity(self, session_id: uuid.UUID) -> bool:
        stmt = update(UserSession).where(UserSession.id == session_id).values(
            last_activity=datetime.utcnow()
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def cleanup_expired_sessions(self) -> int:
        stmt = update(UserSession).where(
            UserSession.expires_at <= datetime.utcnow()
        ).values(is_active=False)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount


class OperatorRepository(BaseRepo):
    async def get_by_id(self, operator_id: uuid.UUID) -> Optional[Operator]:
        stmt = select(Operator).where(Operator.id == operator_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[Operator]:
        stmt = select(Operator).where(Operator.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_operator_code(self, operator_code: str) -> Optional[Operator]:
        stmt = select(Operator).where(Operator.operator_code == operator_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_available_operators(self) -> List[Operator]:
        stmt = select(Operator).where(
            and_(
                Operator.is_available == True,
                Operator.current_load < Operator.max_concurrent_chats
            )
        ).order_by(Operator.current_load.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, operator_data: dict) -> Operator:
        operator = Operator(**operator_data)
        self.session.add(operator)
        await self.session.commit()
        await self.session.refresh(operator)
        return operator

    async def update_load(self, operator_id: uuid.UUID, load_change: int) -> Optional[Operator]:
        operator = await self.get_by_id(operator_id)
        if operator:
            operator.current_load += load_change
            await self.session.commit()
            await self.session.refresh(operator)
        return operator

    async def update_availability(self, operator_id: uuid.UUID, is_available: bool) -> Optional[Operator]:
        operator = await self.get_by_id(operator_id)
        if operator:
            operator.is_available = is_available
            await self.session.commit()
            await self.session.refresh(operator)
        return operator