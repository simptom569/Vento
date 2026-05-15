from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.chat import Chat
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository


@dataclass
class GetUserChatsQuery:
    actor_id: UUID


class GetUserChatsHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, query: GetUserChatsQuery) -> list[Chat]:
        user_memberships = await self.chat_member_repo.get_user_memberships(query.actor_id)
        chat_ids = [m.chat_id for m in user_memberships]
        chats = await self.chat_repo.get_by_ids(chat_ids)
        
        return chats