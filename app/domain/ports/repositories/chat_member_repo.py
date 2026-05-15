from abc import ABC, abstractmethod
from uuid import UUID
from datetime import datetime

from app.domain.entities.chat import ChatMember
from app.domain.entities.enums import ChatRole


class AbstractChatMemberRepository(ABC):
    
    @abstractmethod
    async def get_member(self, user_id: UUID, chat_id: UUID) -> ChatMember | None:
        """Получить участника чата. None если не найден"""
        ...
    
    @abstractmethod
    async def get_chat_members(
        self,
        chat_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatMember]:
        """Получить участников чата."""
        ...
    
    @abstractmethod
    async def save(self, chat_member: ChatMember) -> ChatMember:
        """Создать или обновить подписку на Чат или Канал"""
        ...
    
    @abstractmethod
    async def delete(self, user_id: UUID, chat_id: UUID) -> None:
        """Удалить участника из Чата или Канала"""
        ...
    
    @abstractmethod
    async def get_member_including_deleted(self, user_id: UUID, chat_id: UUID) -> ChatMember | None:
        """Получить участника включая удалённых (для восстановления чата)"""
        ...
    
    @abstractmethod
    async def get_user_memberships(self, user_id: UUID) -> list[ChatMember]:
        """Получить все активные чаты пользователя"""
        ...