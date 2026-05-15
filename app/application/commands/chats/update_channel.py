from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import NotFoundError, ForbiddenError


@dataclass
class UpdateChannelCommand:
    actor_id: UUID
    chat_id: UUID
    title: str | None = None
    username: str | None = None
    is_public: bool | None = None
    avatar_url: str | None = None
    discussion_chat_id: UUID | None = None


class UpdateChannelHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: UpdateChannelCommand) -> None:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        if chat.type not in (ChatType.CHANNEL,):
            raise ForbiddenError("Нельзя изменить данный тип Чата")
        
        user = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not user:
            raise ForbiddenError("Вы не являетесь подписчиком данного Канала")
        
        if user.role not in (ChatRole.OWNER,):
            raise ForbiddenError("Недостаточно прав на изменение Канала")
        
        chat.update(
            title=cmd.title,
            username=cmd.username,
            is_public=cmd.is_public,
            avatar_url=cmd.avatar_url,
            discussion_chat_id=cmd.discussion_chat_id,
        )
        
        await self.chat_repo.save(chat)