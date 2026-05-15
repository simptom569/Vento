from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
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

from app.domain.entities.enums import ChatRole, ChatType
from app.infrastructure.db.models.base import Base, TimestampMixin


class ChatModel(Base, TimestampMixin):
    __tablename__ = "chats"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    type: Mapped[ChatType] = mapped_column(
        Enum(ChatType, name="chat_type"),
        default=ChatType.PRIVATE,
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)
    username: Mapped[str | None] = mapped_column(VARCHAR(32), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(TEXT)
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_public: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    is_verified: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    is_encrypted: Mapped[bool] = mapped_column(BOOLEAN, default=True)
    member_count: Mapped[int] = mapped_column(INTEGER, default=0)
    discussion_chat_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("chats.id", ondelete="SET NULL"),
        nullable=True,
    )


class ChatMembersModel(Base):
    __tablename__ = "chat_members"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="chat_role"),
        default=ChatRole.MEMBER,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_archived: Mapped[bool] = mapped_column(BOOLEAN, default=False)
    last_read_message_seq: Mapped[int] = mapped_column(INTEGER, default=0)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_before_message_seq: Mapped[int] = mapped_column(INTEGER, default=0)
    
    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="uq_chat_members_chat_user"),
    )