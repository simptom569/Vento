from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class AbstractUserRepository(ABC):
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Получить юзера по ID. None если не найден"""
        ...
    
    @abstractmethod
    async def get_by_phone(self, phone_number: str) -> User | None:
        """Получить юзера по номеру телефона - для логина"""
        ...
    
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Получить юзера по @юзернейм - для поиска"""
        ...
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Создать или обновить юзера"""
        ...
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Мягкое удаление юзера"""
        ...
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[User]:
        """Поиск юзера по юзернейм или имени"""
        ...
    
    @abstractmethod
    async def search_contacts(self, owner_user_id: UUID, query: str, limit: int = 10) -> list[User]:
        """Поиск юзера из контактов"""
        ...