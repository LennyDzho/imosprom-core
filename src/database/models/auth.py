from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.database.models import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    operator_profile = relationship("Operator", back_populates="user", uselist=False)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String(512), unique=True, nullable=False, index=True)
    refresh_token = Column(String(512), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")


class Operator(Base):
    __tablename__ = "operators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    operator_code = Column(String(50), unique=True, nullable=False)
    department = Column(String(100))
    max_concurrent_chats = Column(Integer, default=5)
    current_load = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    skills = Column(Text)  # JSON string with operator skills
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="operator_profile")
    escalation_cards = relationship("EscalationCard", back_populates="assigned_operator")