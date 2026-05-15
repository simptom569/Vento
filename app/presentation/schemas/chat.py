from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from app.domain.entities.enums import ChatType, ChatRole


class GroupRequest(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    avatar_url: str | None = None
    is_public: bool = False


class GroupResponse(BaseModel):
    id: UUID
    type: ChatType
    created_by: UUID
    created_at: datetime
    title: str
    avatar_url: str | None
    is_public: bool
    
    @classmethod
    def from_domain(cls, chat) -> "GroupResponse":
        return cls(
            id=chat.id,
            type=chat.type,
            created_by=chat.created_by,
            created_at=chat.created_at,
            title=chat.title,
            avatar_url=chat.avatar_url,
            is_public=chat.is_public
        )


class ChannelRequest(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    username: str | None = Field(default=None, min_length=1, max_length=32)
    avatar_url: str | None = None
    is_public: bool = False


class ChannelResponse(BaseModel):
    id: UUID
    type: ChatType
    created_by: UUID
    created_at: datetime
    title: str
    username: str | None
    avatar_url: str | None
    is_public: bool
    
    @classmethod
    def from_domain(cls, chat) -> "ChannelResponse":
        return cls(
            id=chat.id,
            type=chat.type,
            created_by=chat.created_by,
            created_at=chat.created_at,
            title=chat.title,
            username=chat.username,
            avatar_url=chat.avatar_url,
            is_public=chat.is_public,
        )


class PrivateRequest(BaseModel):
    user_id: UUID


class PrivateResponse(BaseModel):
    id: UUID
    type: ChatType
    created_by: UUID
    created_at: datetime
    
    @classmethod
    def from_domain(cls, chat) -> "PrivateResponse":
        return cls(
            id=chat.id,
            type=chat.type,
            created_by=chat.created_by,
            created_at=chat.created_at,
        )


class ChatListItemResponse(BaseModel):
    id: UUID
    type: ChatType
    title: str | None
    username: str | None
    avatar_url: str | None
    is_public: bool
    member_count: int
    
    @classmethod
    def from_domain(cls, chat) -> "ChatListItemResponse":
        return cls(
            id=chat.id,
            type=chat.type,
            title=chat.title,
            username=chat.username,
            avatar_url=chat.avatar_url,
            is_public=chat.is_public,
            member_count=chat.member_count,
        )


class ChatResponse(BaseModel):
    id: UUID
    type: ChatType
    title: str | None
    username: str | None
    avatar_url: str | None
    is_public: bool
    member_count: int
    
    @classmethod
    def from_domain(cls, chat) -> "ChatResponse":
        return cls(
            id=chat.id,
            type=chat.type,
            title=chat.title,
            username=chat.username,
            avatar_url=chat.avatar_url,
            is_public=chat.is_public,
            member_count=chat.member_count,
        )


class DeleteChatRequest(BaseModel):
    deleted_for_everyone: bool


class UpdateGroupRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    avatar_url: str | None = None


class UpdateChannelRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    username: str | None = Field(default=None, min_length=1, max_length=32)
    is_public: bool | None = None
    avatar_url: str | None = None
    discussion_chat_id: UUID | None = None


class MuteChatRequest(BaseModel):
    time: datetime


class AddMemberRequest(BaseModel):
    user_id: UUID
    role: ChatRole = ChatRole.MEMBER


class AddMemberResponse(BaseModel):
    id: UUID
    chat_id: UUID
    user_id: UUID
    joined_at: datetime
    role: ChatRole
    
    @classmethod
    def from_domain(cls, chat_member) -> "AddMemberResponse":
        return cls(
            id=chat_member.id,
            chat_id=chat_member.chat_id,
            user_id=chat_member.user_id,
            joined_at=chat_member.joined_at,
            role=chat_member.role,
        )


class ChangeMemberRequest(BaseModel):
    role: ChatRole


class ChangeMemberResponse(BaseModel):
    id: UUID
    chat_id: UUID
    user_id: UUID
    role: ChatRole
    
    @classmethod
    def from_domain(cls, chat_member) -> "ChangeMemberResponse":
        return cls(
            id=chat_member.id,
            chat_id=chat_member.chat_id,
            user_id=chat_member.user_id,
            role=chat_member.role,
        )


class ChatMemberListItemResponse(BaseModel):
    id: UUID
    chat_id: UUID
    user_id: UUID
    role: ChatRole
    
    @classmethod
    def from_domain(cls, chat_member) -> "ChatMemberListItemResponse":
        return cls(
            id=chat_member.id,
            chat_id=chat_member.chat_id,
            user_id=chat_member.user_id,
            role=chat_member.role,
        )