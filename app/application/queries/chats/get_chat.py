from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.chat import Chat
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class GetChatQuery:
    actor_id: UUID
    chat_id: UUID


class GetChatHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, query: GetChatQuery) -> Chat:
        chat = await self.chat_repo.get_by_id(query.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        if chat.is_public:
            return chat
        
        user = await self.chat_member_repo.get_member(query.actor_id, query.chat_id)
        if not user:
            raise ForbiddenError("У вас нет доступа к данному Чату")
        
        return chat