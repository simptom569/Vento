from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import (
    INET,
    JSONB,
)
from sqlalchemy import (
    BigInteger,
    BOOLEAN,
    DateTime,
    Enum,
    ForeignKey,
    INTEGER,
    TEXT,
    VARCHAR,
    func,
    UniqueConstraint,
)

from app.domain.entities.enums import PrivacyVisibility, TwoFAMethod, Platform
from app.infrastructure.db.models.base import Base, TimestampMixin


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    phone_number: Mapped[str] = mapped_column(VARCHAR(20), unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(VARCHAR(32), unique=True)
    display_name: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    bio: Mapped[str | None] = mapped_column(TEXT)
    avatar_url: Mapped[str | None] = mapped_column(TEXT)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_online: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    is_deleted: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    
    settings: Mapped["UserSettingsModel"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    

class UserSettingsModel(Base):
    __tablename__ = "user_settings"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    privacy_last_seen: Mapped[PrivacyVisibility] = mapped_column(
        Enum(PrivacyVisibility, name="privacy_visibility"),
        default=PrivacyVisibility.EVERYONE,
        nullable=False
    )
    privacy_avatar: Mapped[PrivacyVisibility] = mapped_column(
        Enum(PrivacyVisibility, name="privacy_visibility"),
        default=PrivacyVisibility.EVERYONE,
        nullable=False
    )
    privacy_phone: Mapped[PrivacyVisibility] = mapped_column(
        Enum(PrivacyVisibility, name="privacy_visibility"),
        default=PrivacyVisibility.CONTACTS,
        nullable=False
    )
    notifications_enabled: Mapped[bool] = mapped_column(BOOLEAN, default=True)
    two_fa_method: Mapped[TwoFAMethod] = mapped_column(
        Enum(TwoFAMethod, name="two_fa_method"),
        default=TwoFAMethod.NONE,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["UserModel"] = relationship(back_populates="settings")


class AuthSessionModel(Base):
    __tablename__ = "auth_sessions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    device_name: Mapped[str | None] = mapped_column(VARCHAR(128))
    family_id: Mapped[UUID] = mapped_column(nullable=False)
    platform: Mapped[str | None] = mapped_column(
        Enum(Platform, name="platform")
    )
    push_token: Mapped[str | None] = mapped_column(TEXT)
    refresh_token_hash: Mapped[str] = mapped_column(TEXT, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    user: Mapped["UserModel"] = relationship()


class UserContactModel(Base):
    __tablename__ = "user_contacts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    custom_name: Mapped[str | None] = mapped_column(VARCHAR(64))
    is_blocked: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    owner: Mapped["UserModel"] = relationship(foreign_keys=[owner_user_id])
    contact: Mapped["UserModel"] = relationship(foreign_keys=[contact_user_id])
    
    __table_args__ = (
        UniqueConstraint("owner_user_id", "contact_user_id", name="uq_user_contacts_owner_contact"),
    )


class UserKeyModel(Base):
    __tablename__ = "user_keys"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[str] = mapped_column(VARCHAR(128), nullable=False)
    key_type: Mapped[str] = mapped_column(VARCHAR(32), nullable=False)
    public_key: Mapped[str] = mapped_column(TEXT, nullable=False)
    signed_pre_key: Mapped[str] = mapped_column(TEXT, nullable=False)
    one_time_pre_keys: Mapped[dict] = mapped_column(JSONB, nullable=True)
    one_time_pre_keys_count: Mapped[int] = mapped_column(INTEGER, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    
    user: Mapped["UserModel"] = relationship()
    
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_user_keys_user_device"),
    )


class UserCredentialModel(Base):
    __tablename__ = "user_credentials"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    user: Mapped["UserModel"] = relationship()


class EncryptedBackupModel(Base):
    __tablename__ = "encrypted_backups"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    encrypted_data: Mapped[str] = mapped_column(TEXT, nullable=False)
    version: Mapped[int] = mapped_column(INTEGER, default=1)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["UserModel"] = relationship()