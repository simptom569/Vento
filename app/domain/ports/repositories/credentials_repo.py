from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.session import AuthSession


class AbstractCredentialsRepository(ABC):
    
    @abstractmethod
    async def save_password(self, user_id: UUID, password_hash: str) -> None:
        ...
    
    @abstractmethod
    async def get_password_hash(self, user_id: UUID) -> str | None:
        ...
    
    @abstractmethod
    async def save_session(
        self,
        user_id: UUID,
        device_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
        family_id: UUID,
        device_name: str | None = None,
        platform: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        ...
    
    @abstractmethod
    async def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        ...
    
    @abstractmethod
    async def get_session_by_family(self, family_id: UUID) -> AuthSession | None:
        """Ищем активную сессию в семье"""
        ...
    
    @abstractmethod
    async def delete_session(self, session_id: UUID) -> None:
        ...
    
    @abstractmethod
    async def delete_sessions_by_family(self, family_id: UUID) -> None:
        """Инвалидируем все сессии при детектировании кражи"""
        ...
    
    @abstractmethod
    async def delete_all_user_sessions(self, user_id: UUID) -> None:
        ...
    
    @abstractmethod
    async def upsert_session(
        self,
        user_id: UUID,
        device_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
        family_id: UUID,
        device_name: str | None = None,
        platform: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        """
        Обновляем сессию есть device_id уже есть у пользователя,
        иначе создаем с нуля. Предотвращение накопление сессий одного устройства.
        """
        ...