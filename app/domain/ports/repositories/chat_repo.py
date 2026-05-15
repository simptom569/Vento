from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.chat import Chat


class AbstractChatRepository(ABC):
    
    @abstractmethod
    async def get_by_id(self, chat_id: UUID) -> Chat | None:
        """Получить чат по ID. None если не найден"""
        ...
    
    @abstractmethod
    async def get_by_ids(self, chat_ids: list[UUID]) -> list[Chat]:
        """Получить несколько чатов по спику ID."""
        ...
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Chat | None:
        """Получить чат по @юзернейм - для поиска"""
        ...
    
    @abstractmethod
    async def save(self, chat: Chat) -> Chat:
        """Создать или обновить Чат"""
        ...
    
    @abstractmethod
    async def delete(self, chat_id: UUID) -> None:
        """Удаление чата"""
        ...
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[Chat]:
        """Поиск чата по юзернейм или имени"""
        ...
    
    @abstractmethod
    async def get_user_chats(self, user_id: UUID) -> list[Chat]:
        """Получить все чаты пользователя"""
        ...
    
    @abstractmethod
    async def get_private_chat(self, user_id: UUID, other_user_id: UUID) -> Chat | None:
        """Найти личный чат между двумя пользователями"""
        ...
    
    @abstractmethod
    async def get_private_chat_including_deleted(self, user_id: UUID, other_user_id: UUID) -> Chat | None:
        """Найти личный чат включая те где один из участников сделал soft delete"""
        ...