from pydantic import BaseModel
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    phone_number: str
    display_name: str
    username: str | None
    bio: str | None
    avatar_url: str | None
    is_online: bool
    
    @classmethod
    def from_domain(cls, user) -> "UserResponse":
        return cls(
            id=user.id,
            phone_number=user.phone_number,
            display_name=user.display_name,
            username=user.username,
            bio=user.bio,
            avatar_url=user.avatar_url,
            is_online=user.is_online,
        )