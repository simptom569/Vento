from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.session import AuthSession
from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.infrastructure.db.models.user import AuthSessionModel, UserCredentialModel


class CredentialsRepository(AbstractCredentialsRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_password(self, user_id: UUID, password_hash: str) -> None:
        credential = UserCredentialModel(
            id=uuid4(),
            user_id=user_id,
            password_hash=password_hash,
        )
        self.session.add(credential)
        await self.session.commit()
    
    async def get_password_hash(self, user_id: UUID) -> str | None:
        result = await self.session.execute(
            select(UserCredentialModel.password_hash)
            .where(UserCredentialModel.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def upsert_session(
        self,
        user_id: UUID,
        device_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
        family_id: UUID,
        device_name: str | None = None,
        platform: str | None = None,
        ip_address: str | None = None
    ) -> None:
        existing = await self.session.execute(
            select(AuthSessionModel)
            .where(AuthSessionModel.user_id == user_id)
            .where(AuthSessionModel.device_id == device_id)
        )
        db_session = existing.scalar_one_or_none()
        
        if db_session:
            db_session.refresh_token_hash = refresh_token_hash
            db_session.expires_at = expires_at
            db_session.family_id = family_id
            db_session.last_used_at = datetime.now(UTC)
            db_session.ip_address = ip_address
        else:
            db_session = AuthSessionModel(
                id=uuid4(),
                user_id=user_id,
                device_id=device_id,
                device_name=device_name,
                platform=platform,
                family_id=family_id,
                refresh_token_hash=refresh_token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
            )
            self.session.add(db_session)
        
        await self.session.commit()
    
    async def save_session(
        self,
        user_id: UUID,
        device_id: str,
        refresh_token_hash: str,
        expires_at: datetime,
        family_id: UUID,
        device_name: str | None = None,
        platform: str | None = None,
        ip_address: str | None = None
    ) -> None:
        db_session = AuthSessionModel(
            id=uuid4(),
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            family_id=family_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
        )
        self.session.add(db_session)
        await self.session.commit()
    
    async def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSessionModel)
            .where(AuthSessionModel.refresh_token_hash == token_hash)
        )
        db_session = result.scalar_one_or_none()
        return self._to_entity(db_session) if db_session else None
    
    async def get_session_by_family(self, family_id: UUID) -> AuthSession | None:
        result = await self.session.execute(
            select(AuthSessionModel)
            .where(AuthSessionModel.family_id == family_id)
        )
        db_session = result.scalar_one_or_none()
        return self._to_entity(db_session) if db_session else None
    
    async def delete_session(self, session_id: UUID) -> None:
        await self.session.execute(
            delete(AuthSessionModel)
            .where(AuthSessionModel.id == session_id)
        )
        await self.session.commit()
    
    async def delete_sessions_by_family(self, family_id: UUID) -> None:
        await self.session.execute(
            delete(AuthSessionModel)
            .where(AuthSessionModel.family_id == family_id)
        )
        await self.session.commit()
    
    async def delete_all_user_sessions(self, user_id: UUID) -> None:
        await self.session.execute(
            delete(AuthSessionModel)
            .where(AuthSessionModel.user_id == user_id)
        )
        await self.session.commit()
    
    def _to_entity(self, db_session: AuthSessionModel) -> AuthSession:
        return AuthSession(
            id=db_session.id,
            user_id=db_session.user_id,
            device_id=db_session.device_id,
            device_name=db_session.device_name,
            platform=db_session.platform,
            ip_address=db_session.ip_address,
            expires_at=db_session.expires_at,
            family_id=db_session.family_id,
        )