from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime, UTC

from app.domain.entities.enums import PrivacyVisibility, TwoFAMethod


@dataclass
class UserSettings:
    privacy_last_seen: PrivacyVisibility = PrivacyVisibility.EVERYONE
    privacy_avatar: PrivacyVisibility = PrivacyVisibility.EVERYONE
    privacy_phone: PrivacyVisibility = PrivacyVisibility.CONTACTS
    notification_enabled: bool = True
    two_fa_method: TwoFAMethod = TwoFAMethod.NONE


@dataclass
class User:
    id: UUID
    phone_number: str
    display_name: str
    created_at: datetime
    username: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    last_seen_at: datetime | None = None
    is_online: bool = False
    is_deleted: bool = False
    updated_at: datetime | None = None
    settings: UserSettings = field(default_factory=UserSettings)
    
    def block(self) -> None:
        self.is_deleted = True
    
    def go_online(self) -> None:
        self.is_online = True
    
    def go_offline(self) -> None:
        self.is_online = False
        self.last_seen_at = datetime.now(UTC)
    
    def update_profile(
        self,
        display_name: str | None = None,
        bio: str | None = None,
        username: str | None = None,
    ) -> None:
        if display_name is not None:
            self.display_name = display_name
        if bio is not None:
            self.bio = bio
        if username is not None:
            self.username = username
        self.updated_at = datetime.now(UTC)
