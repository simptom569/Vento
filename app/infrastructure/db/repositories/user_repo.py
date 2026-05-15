from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select

from app.domain.entities.user import User, UserSettings
from app.domain.entities.enums import PrivacyVisibility, TwoFAMethod
from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.infrastructure.db.models.user import UserModel, UserSettingsModel, UserContactModel


class UserRepository(AbstractUserRepository):
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(UserModel)
            .options(joinedload(UserModel.settings))
            .where(UserModel.id == user_id)
            .where(UserModel.is_deleted == False)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_entity(db_user)
    
    async def get_by_phone(self, phone_number: str) -> User | None:
        result = await self.session.execute(
            select(UserModel)
            .options(joinedload(UserModel.settings))
            .where(UserModel.phone_number == phone_number)
            .where(UserModel.is_deleted == False)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_entity(db_user)
    
    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(UserModel)
            .options(joinedload(UserModel.settings))
            .where(UserModel.username == username)
            .where(UserModel.is_deleted == False)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_entity(db_user)
    
    async def save(self, user: User) -> User:
        db_user = await self.session.get(UserModel, user.id)
        
        if not db_user:
            db_user = UserModel(
                id=user.id,
                phone_number=user.phone_number,
                display_name=user.display_name,
                username=user.username,
                bio=user.bio,
                avatar_url=user.avatar_url,
                is_online=user.is_online,
                is_deleted=user.is_deleted,
            )
            self.session.add(db_user)
            await self.session.flush()
            
            db_settings = UserSettingsModel(
                user_id=user.id,
                privacy_last_seen=user.settings.privacy_last_seen,
                privacy_avatar=user.settings.privacy_avatar,
                privacy_phone=user.settings.privacy_phone,
                notifications_enabled=user.settings.notification_enabled,
                two_fa_method=user.settings.two_fa_method,
            )
            self.session.add(db_settings)
        else:
            db_user.display_name = user.display_name
            db_user.username = user.username
            db_user.bio = user.bio
            db_user.avatar_url = user.avatar_url
            db_user.is_online = user.is_online
            db_user.is_deleted = user.is_deleted
        
        await self.session.commit()
        return user

    async def delete(self, user_id: UUID) -> None:
        db_user = await self.session.get(UserModel, user_id)
        if db_user:
            db_user.is_deleted = True
            await self.session.commit()
    
    async def search(self, query: str, limit: int = 10) -> list[User]:
        result = await self.session.execute(
            select(UserModel)
            .options(joinedload(UserModel.settings))
            .where(UserModel.is_deleted == False)
            .where(
                UserModel.username.ilike(f"%{query}%") |
                UserModel.display_name.ilike(f"%{query}%")
            )
            .limit(limit)
        )
        return [self._to_entity(u) for u in result.scalars().all()]
    
    async def search_contacts(self, actor_id: UUID, query: str, limit: int = 10) -> list[User]:
        result = await self.session.execute(
            select(UserModel)
            .options(joinedload(UserModel.settings))
            .join(UserContactModel, UserContactModel.contact_user_id == UserModel.id)
            .where(UserModel.is_deleted == False)
            .where(UserContactModel.owner_user_id == actor_id)
            .where(UserContactModel.is_blocked == False)
            .where(
                UserModel.username.ilike(f"%{query}%") |
                UserModel.display_name.ilike(f"%{query}%") |
                UserContactModel.custom_name.ilike(f"%{query}%")
            )
            .limit(limit)
        )
        return [self._to_entity(u) for u in result.scalars().all()]
    
    def _to_entity(self, db_user: UserModel) -> User:
        settings = UserSettings()
        if db_user.settings:
            settings = UserSettings(
                privacy_last_seen=db_user.settings.privacy_last_seen,
                privacy_avatar=db_user.settings.privacy_avatar,
                privacy_phone=db_user.settings.privacy_phone,
                notification_enabled=db_user.settings.notifications_enabled,
                two_fa_method=db_user.settings.two_fa_method,
            )
        return User(
            id=db_user.id,
            phone_number=db_user.phone_number,
            display_name=db_user.display_name,
            created_at=db_user.created_at,
            username=db_user.username,
            bio=db_user.bio,
            avatar_url=db_user.avatar_url,
            last_seen_at=db_user.last_seen_at,
            is_online=db_user.is_online,
            is_deleted=db_user.is_deleted,
            updated_at=db_user.updated_at,
            settings=settings,
        )