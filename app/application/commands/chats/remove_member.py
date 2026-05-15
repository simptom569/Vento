from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.enums import ChatType, ChatRole
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class RemoveMemberCommand:
    chat_id: UUID
    actor_id: UUID
    user_id: UUID


class RemoveMemberHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: RemoveMemberCommand) -> None:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        actor = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not actor:
            raise ForbiddenError("Вы не состоите в этом чате")
        
        if chat.type not in (ChatType.CHANNEL, ChatType.GROUP,):
            raise ForbiddenError("Нельзя удалить участника из данного типа чата")
            
        user = await self.chat_member_repo.get_member(cmd.user_id, cmd.chat_id)
        if not user:
            raise ForbiddenError("Юзер не состоит в данном Чате или Канале")
        
        if actor.role not in (ChatRole.OWNER, ChatRole.ADMIN,):
            raise ForbiddenError("У вас нет прав для исключения юзера их Чата или Канала")
            
        chat.remove_member()
        await self.chat_repo.save(chat)
        await self.chat_member_repo.delete(cmd.user_id, cmd.chat_id)