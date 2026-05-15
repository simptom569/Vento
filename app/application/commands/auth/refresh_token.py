from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.domain.exceptions import ForbiddenError, TokenTheftError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.config import settings


@dataclass
class RefreshTokenCommand:
    refresh_token: str


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class RefreshTokenHandler:
    def __init__(self, credentials_repo: AbstractCredentialsRepository):
        self.credentials_repo = credentials_repo
    
    async def handle(self, cmd: RefreshTokenCommand) -> TokenPair:
        token_hash = hash_refresh_token(cmd.refresh_token)
        session = await self.credentials_repo.get_session_by_token_hash(token_hash)
        
        if not session:
            raise ForbiddenError("Недействительный refresh токен")
        
        if session.expires_at.replace(tzinfo=None if session.expires_at.tzinfo else None) < datetime.now(UTC).replace(tzinfo=None):
            await self.credentials_repo.delete_session(session.id)
            raise ForbiddenError("Refresh токен истек")
        
        await self.credentials_repo.delete_session(session.id)
        
        existing_in_family = await self.credentials_repo.get_session_by_family(session.family_id)
        if existing_in_family:
            await self.credentials_repo.delete_sessions_by_family(session.family_id)
            raise TokenTheftError("Обнаружено повторное использование токена. Все сессии инвалидированы.")
        
        new_raw_refresh = generate_refresh_token()
        new_expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        await self.credentials_repo.save_session(
            user_id=session.user_id,
            device_id=session.device_id,
            refresh_token_hash=hash_refresh_token(new_raw_refresh),
            expires_at=new_expires_at,
            family_id=session.family_id,
            device_name=session.device_name,
            platform=session.platform,
            ip_address=session.ip_address,
        )
        
        return TokenPair(
            access_token=create_access_token(session.user_id),
            refresh_token=new_raw_refresh,
        )