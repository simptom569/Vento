from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, UTC

from app.domain.entities.enums import ChatType, ChatRole


@dataclass
class ChatMember:
    id: UUID
    chat_id: UUID
    user_id: UUID
    joined_at: datetime
    role: ChatRole = ChatRole.MEMBER
    muted_until: datetime | None = None
    is_archived: bool = False
    last_read_message_seq: int = 0
    deleted_before_message_seq: int = 0
    deleted_at: datetime | None = None

    def add_to_archive(self) -> None:
        self.is_archived = True
    
    def remove_from_archive(self) -> None:
        self.is_archived = False
    
    def mute(self, until: datetime) -> None:
        self.muted_until = until
    
    def unmute(self) -> None:
        self.muted_until = None
    
    def change_role(self, role: ChatRole) -> None:
        self.role = role
        
    def soft_delete(self, last_message_seq: int) -> None:
        self.deleted_at = datetime.now(UTC)
        self.deleted_before_message_seq = last_message_seq
    
    def restore(self) -> None:
        self.deleted_at = None


@dataclass
class Chat:
    id: UUID
    type: ChatType
    created_by: UUID
    created_at: datetime
    title: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    is_public: bool = False
    is_verified: bool = False
    is_encrypted: bool = True
    member_count: int = 0
    discussion_chat_id: UUID | None = None
    updated_at: datetime | None = None
    
    def add_member(self) -> None:
        self.member_count += 1
        self.updated_at = datetime.now(UTC)
    
    def remove_member(self) -> None:
        if self.member_count > 0:
            self.member_count -= 1
        self.updated_at = datetime.now(UTC)
    
    def update(
        self,
        title: str | None = None,
        username: str | None = None,
        is_public: bool | None = None,
        avatar_url: str | None = None,
        discussion_chat_id: UUID | None = None,
    ) -> None:
        if title is not None:
            self.title = title
        if username is not None:
            self.username = username
        if is_public is not None:
            self.is_public = is_public
        if avatar_url is not None:
            self.avatar_url = avatar_url
        if discussion_chat_id is not None:
            self.discussion_chat_id = discussion_chat_id
        self.updated_at = datetime.now(UTC)