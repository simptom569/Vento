from dataclasses import dataclass
from uuid import uuid4
from datetime import datetime, UTC

from app.domain.entities.user import User, UserSettings
from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.domain.exceptions import AlreadyExistsError
from app.core.security import hash_password


@dataclass
class RegisterCommand:
    phone_number: str
    display_name: str
    password: str


class RegisterHandler:
    def __init__(
        self,
        user_repo: AbstractUserRepository,
        credentials_repo: AbstractCredentialsRepository,
    ):
        self.user_repo = user_repo
        self.credentials_repo = credentials_repo
    
    async def handle(self, cmd: RegisterCommand) -> User:
        existing = await self.user_repo.get_by_phone(cmd.phone_number)
        if existing:
            raise AlreadyExistsError("Номер телефона уже зарегистрирован")

        user = User(
            id=uuid4(),
            phone_number=cmd.phone_number,
            display_name=cmd.display_name,
            created_at=datetime.now(UTC),
            settings=UserSettings(),
        )
        
        await self.user_repo.save(user)
        await self.credentials_repo.save_password(user.id, hash_password(cmd.password))
        
        return user