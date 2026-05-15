from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.domain.entities.chat import ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.infrastructure.db.models.chat import ChatModel, ChatMembersModel


class ChatMemberRepository(AbstractChatMemberRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_member(self, user_id: UUID, chat_id: UUID) -> ChatMember | None:
        result = await self.session.execute(
            select(ChatMembersModel)
            .where(ChatMembersModel.user_id == user_id)
            .where(ChatMembersModel.chat_id == chat_id)
            .where(ChatMembersModel.deleted_at.is_(None))
        )
        db_chat_member = result.scalar_one_or_none()
        if not db_chat_member:
            return None
        return self._to_entity(db_chat_member)
    
    async def get_chat_members(self, chat_id: UUID, limit: int = 50, offset: int = 0) -> list[ChatMember]:
        result = await self.session.execute(
            select(ChatMembersModel)
            .where(ChatMembersModel.chat_id == chat_id)
            .offset(offset)
            .limit(limit)
        )
        return [self._to_entity(c) for c in result.scalars().all()]
    
    async def save(self, chat_member: ChatMember) -> ChatMember:
        db_chat_member = await self.session.get(ChatMembersModel, chat_member.id)
        
        if not db_chat_member:
            db_chat_member = ChatMembersModel(
                id=chat_member.id,
                chat_id=chat_member.chat_id,
                user_id=chat_member.user_id,
                role=chat_member.role,
                joined_at=chat_member.joined_at,
                muted_until=chat_member.muted_until,
                is_archived=chat_member.is_archived,
                last_read_message_seq=chat_member.last_read_message_seq,
                deleted_at=chat_member.deleted_at,
                deleted_before_message_seq=chat_member.deleted_before_message_seq,
            )
            self.session.add(db_chat_member)
            await self.session.flush()
        else:
            db_chat_member.role = chat_member.role
            db_chat_member.muted_until = chat_member.muted_until
            db_chat_member.is_archived = chat_member.is_archived
            db_chat_member.last_read_message_seq = chat_member.last_read_message_seq
            db_chat_member.deleted_before_message_seq = chat_member.deleted_before_message_seq
            db_chat_member.deleted_at = chat_member.deleted_at
        
        await self.session.commit()
        return chat_member
    
    async def delete(self, user_id: UUID, chat_id: UUID) -> None:
        await self.session.execute(
            delete(ChatMembersModel)
            .where(ChatMembersModel.chat_id == chat_id)
            .where(ChatMembersModel.user_id == user_id)
        )
        await self.session.commit()
    
    async def get_member_including_deleted(self, user_id: UUID, chat_id: UUID) -> ChatMember | None:
        result = await self.session.execute(
            select(ChatMembersModel)
            .where(ChatMembersModel.chat_id == chat_id)
            .where(ChatMembersModel.user_id == user_id)
        )
        db_chat_member = result.scalar_one_or_none()
        if not db_chat_member:
            return None
        return self._to_entity(db_chat_member)
    
    async def get_user_memberships(self, user_id: UUID) -> list[ChatMember]:
        result = await self.session.execute(
            select(ChatMembersModel)
            .where(ChatMembersModel.user_id == user_id)
            .where(ChatMembersModel.deleted_at.is_(None))
        )
        return [self._to_entity(c) for c in result.scalars().all()]
    
    def _to_entity(self, db_chat_member: ChatMembersModel) -> ChatMember:
        return ChatMember(
            id=db_chat_member.id,
            chat_id=db_chat_member.chat_id,
            user_id=db_chat_member.user_id,
            joined_at=db_chat_member.joined_at,
            role=db_chat_member.role,
            muted_until=db_chat_member.muted_until,
            is_archived=db_chat_member.is_archived,
            last_read_message_seq=db_chat_member.last_read_message_seq,
            deleted_before_message_seq=db_chat_member.deleted_before_message_seq,
            deleted_at=db_chat_member.deleted_at,
        )