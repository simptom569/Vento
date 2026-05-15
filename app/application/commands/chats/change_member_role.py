from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.chat import ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class ChangeMemberRoleCommand:
    user_id: UUID
    chat_id: UUID
    actor_id: UUID
    role: ChatRole

class ChangeMemberRoleHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: ChangeMemberRoleCommand) -> ChatMember:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        if chat.type in (ChatType.PRIVATE, ChatType.SECRET,):
            raise ForbiddenError("Нельзя изменить роль участника в данном типе чата")
        
        actor = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not actor:
            raise ForbiddenError("Вы не состоите в этом чате")
        if actor.role not in (ChatRole.OWNER,):
            raise ForbiddenError("Недостаточно прав для изменения роли участников")
        
        chat_member = await self.chat_member_repo.get_member(cmd.user_id, cmd.chat_id)
        if not chat_member:
            raise NotFoundError("Пользователь не состоит в чате")
        chat_member.change_role(cmd.role)
        
        await self.chat_member_repo.save(chat_member)
        
        return chat_member