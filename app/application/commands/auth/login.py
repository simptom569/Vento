from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from uuid import UUID, uuid4

from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.domain.exceptions import ForbiddenError
from app.core.security import (
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.core.config import settings


@dataclass
class LoginCommand:
    phone_number: str
    password: str
    device_id: str
    device_name: str | None = None
    platform: str | None = None
    ip_address: str | None = None


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    user_id: UUID


class LoginHandler:
    def __init__(
        self,
        user_repo: AbstractUserRepository,
        credentials_repo: AbstractCredentialsRepository,
    ):
        self.user_repo = user_repo
        self.credentials_repo = credentials_repo
    
    async def handle(self, cmd: LoginCommand) -> TokenPair:
        user = await self.user_repo.get_by_phone(cmd.phone_number)
        
        password_hash = await self.credentials_repo.get_password_hash(user.id) if user else None
        password_valid = verify_password(cmd.password, password_hash) if password_hash else False
        
        if not user or not password_valid:
            raise ForbiddenError("Неверный номер или пароль")
        
        raw_refresh = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        await self.credentials_repo.upsert_session(
            user_id=user.id,
            device_id=cmd.device_id,
            refresh_token_hash=hash_refresh_token(raw_refresh),
            expires_at=expires_at,
            family_id=uuid4(),
            device_name=cmd.device_name,
            platform=cmd.platform,
            ip_address=cmd.ip_address,
        )
        
        return TokenPair(
            access_token=create_access_token(user.id),
            refresh_token=raw_refresh,
            user_id=user.id,
        )