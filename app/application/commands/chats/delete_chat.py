from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.enums import ChatType, ChatRole
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class DeleteChatCommand:
    actor_id: UUID
    chat_id: UUID
    delete_for_everyone: bool = False


class DeleteChatHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: DeleteChatCommand) -> None:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        user = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not user:
            raise ForbiddenError("Вы не состоите в этом чате")
        
        if chat.type in (ChatType.PRIVATE,):
            if cmd.delete_for_everyone:
                await self.chat_repo.delete(cmd.chat_id)
            else:
                user.soft_delete(last_message_seq=0)
                await self.chat_member_repo.save(user)
        
        elif chat.type in (ChatType.CHANNEL,):
            if user.role not in (ChatRole.OWNER,):
                raise ForbiddenError("Только владелец может удалить канал")
            await self.chat_repo.delete(cmd.chat_id)
        
        elif chat.type in (ChatType.GROUP,):
            if cmd.delete_for_everyone:
                if user.role not in (ChatRole.OWNER,):
                    raise ForbiddenError("Удалить группу может только владелец")
                await self.chat_repo.delete(cmd.chat_id)
            else:
                user.soft_delete(last_message_seq=0)
                await self.chat_member_repo.save(user)
         
        elif chat.type in (ChatType.SECRET,):
            await self.chat_repo.delete(cmd.chat_id)