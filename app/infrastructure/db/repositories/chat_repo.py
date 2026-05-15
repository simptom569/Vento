from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.domain.entities.chat import Chat
from app.domain.entities.enums import ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.infrastructure.db.models.chat import ChatModel, ChatMembersModel


class ChatRepository(AbstractChatRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        result = await self.session.execute(
            select(ChatModel)
            .where(ChatModel.id == chat_id)
        )
        db_chat = result.scalar_one_or_none()
        if not db_chat:
            return None
        return self._to_entity(db_chat)
    
    async def get_by_ids(self, chat_ids: list[UUID]) -> list[Chat]:
        result = await self.session.execute(
            select(ChatModel)
            .where(ChatModel.id.in_(chat_ids))
        )
        return [self._to_entity(c) for c in result.scalars().all()]
    
    async def get_by_username(self, username: str) -> Chat | None:
        result = await self.session.execute(
            select(ChatModel)
            .where(ChatModel.username == username)
        )
        db_chat = result.scalar_one_or_none()
        if not db_chat:
            return None
        return self._to_entity(db_chat)
    
    async def save(self, chat: Chat) -> Chat:
        db_chat = await self.session.get(ChatModel, chat.id)
        
        if not db_chat:
            db_chat = ChatModel(
                id=chat.id,
                type=chat.type,
                title=chat.title,
                username=chat.username,
                avatar_url=chat.avatar_url,
                created_by=chat.created_by,
                is_public=chat.is_public,
                is_verified=chat.is_verified,
                is_encrypted=chat.is_encrypted,
                member_count=chat.member_count,
                discussion_chat_id=chat.discussion_chat_id,
            )
            self.session.add(db_chat)
            await self.session.flush()
        else:
            db_chat.title = chat.title
            db_chat.username = chat.username
            db_chat.is_public = chat.is_public
            db_chat.avatar_url = chat.avatar_url
            db_chat.discussion_chat_id = chat.discussion_chat_id
        
        await self.session.commit()
        return chat
    
    async def delete(self, chat_id: UUID) -> None:
        await self.session.execute(
            delete(ChatModel)
            .where(ChatModel.id == chat_id)
        )
        await self.session.commit()
    
    async def search(self, query: str, limit: int = 10) -> list[Chat]:
        result = await self.session.execute(
            select(ChatModel)
            .where(ChatModel.is_public == True)
            .where(
                ChatModel.title.ilike(f"%{query}%") |
                ChatModel.username.ilike(f"%{query}%")
            )
            .limit(limit)
        )
        return [self._to_entity(c) for c in result.scalars().all()]

    async def get_user_chats(self, user_id: UUID) -> list[Chat]:
        result = await self.session.execute(
            select(ChatModel)
            .join(ChatMembersModel, ChatMembersModel.chat_id == ChatModel.id)
            .where(ChatMembersModel.user_id == user_id)
            .where(ChatMembersModel.deleted_at.is_(None))
        )
        return [self._to_entity(c) for c in result.scalars().all()]

    async def get_private_chat(self, user_id: UUID, other_user_id: UUID) -> Chat | None:
        first = (
            select(ChatMembersModel.chat_id)
            .where(ChatMembersModel.user_id == user_id)
            .where(ChatMembersModel.deleted_at.is_(None))
            .scalar_subquery()
        )
        second = (
            select(ChatMembersModel.chat_id)
            .where(ChatMembersModel.user_id == other_user_id)
            .where(ChatMembersModel.deleted_at.is_(None))
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(ChatModel)
            .where(ChatModel.type == ChatType.PRIVATE)
            .where(ChatModel.id.in_(first))
            .where(ChatModel.id.in_(second))
        )
        db_chat = result.scalar_one_or_none()
        if not db_chat:
            return None
        return self._to_entity(db_chat)
    
    async def get_private_chat_including_deleted(self, user_id: UUID, other_user_id: UUID) -> Chat | None:
        first = (
            select(ChatMembersModel.chat_id)
            .where(ChatMembersModel.user_id == user_id)
            .scalar_subquery()
        )
        second = (
            select(ChatMembersModel.chat_id)
            .where(ChatMembersModel.user_id == other_user_id)
            .scalar_subquery()
        )
        result = await self.session.execute(
            select(ChatModel)
            .where(ChatModel.type == ChatType.PRIVATE)
            .where(ChatModel.id.in_(first))
            .where(ChatModel.id.in_(second))
        )
        db_chat = result.scalar_one_or_none()
        if not db_chat:
            return None
        return self._to_entity(db_chat)

    def _to_entity(self, db_chat: ChatModel) -> Chat:
        return Chat(
            id=db_chat.id,
            type=db_chat.type,
            created_by=db_chat.created_by,
            created_at=db_chat.created_at,
            title=db_chat.title,
            username=db_chat.username,
            avatar_url=db_chat.avatar_url,
            is_public=db_chat.is_public,
            is_verified=db_chat.is_verified,
            is_encrypted=db_chat.is_encrypted,
            member_count=db_chat.member_count,
            discussion_chat_id=db_chat.discussion_chat_id,
            updated_at=db_chat.updated_at,
        )