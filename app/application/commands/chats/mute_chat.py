from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class MuteChatCommand:
    actor_id: UUID
    chat_id: UUID
    time: datetime


class MuteChatHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: MuteChatCommand) -> None:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        chat_member = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not chat_member:
            raise ForbiddenError("Вы не состоите в этом чате")
        
        chat_member.mute(cmd.time)
        await self.chat_member_repo.save(chat_member)