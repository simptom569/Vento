from dataclasses import dataclass

from app.domain.ports.repositories.credentials_repo import AbstractCredentialsRepository
from app.domain.exceptions import ForbiddenError
from app.core.security import hash_refresh_token


@dataclass
class LogoutCommand:
    refresh_token: str


class LogoutHandler:
    def __init__(self, credentials_repo: AbstractCredentialsRepository):
        self.credentials_repo = credentials_repo
    
    async def handle(self, cmd: LogoutCommand) -> None:
        token_hash = hash_refresh_token(cmd.refresh_token)
        session = await self.credentials_repo.get_session_by_token_hash(token_hash)
        
        if not session:
            return
        
        await self.credentials_repo.delete_session(session.id)