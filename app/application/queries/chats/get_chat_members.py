from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.chat import ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class GetChatMembersQuery:
    actor_id: UUID
    chat_id: UUID


class GetChatMembersHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, query: GetChatMembersQuery) -> list[ChatMember]:
        chat = await self.chat_repo.get_by_id(query.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        user = await self.chat_member_repo.get_member(query.actor_id, query.chat_id)
        if not user:
            raise ForbiddenError("Вы не состоите в чате")
        
        if chat.type in (ChatType.PRIVATE, ChatType.SECRET,):
            raise ForbiddenError("Нельзя получить участников данного типа чата")
        
        elif chat.type in (ChatType.CHANNEL,):
            if user.role not in (ChatRole.OWNER, ChatRole.ADMIN,):
                raise ForbiddenError("У вас нет прав для просмотра пользователей в данном Канале")
        
        members = await self.chat_member_repo.get_chat_members(query.chat_id)
        
        return members