from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.enums import ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class LeaveChatCommand:
    actor_id: UUID
    chat_id: UUID


class LeaveChatHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: LeaveChatCommand) -> None:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        if chat.type not in (ChatType.CHANNEL, ChatType.GROUP,):
            raise ForbiddenError("Нельзя выйти из данного типа Чата")
        
        user = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not user:
            raise ForbiddenError("Вы не состоите в этом Чате")
        
        chat.remove_member()
        
        await self.chat_member_repo.delete(cmd.actor_id, cmd.chat_id)
        await self.chat_repo.save(chat)