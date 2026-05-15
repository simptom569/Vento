from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AuthSession:
    id: UUID
    user_id: UUID
    device_id: str
    family_id: UUID
    expires_at: datetime
    device_name: str | None = None
    platform: str | None = None
    ip_address: str | None = None