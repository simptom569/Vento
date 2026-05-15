from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.domain.entities.chat import ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.domain.exceptions import AlreadyExistsError, NotFoundError, ForbiddenError


@dataclass
class AddMemberCommand:
    user_id: UUID
    chat_id: UUID
    actor_id: UUID
    role: ChatRole = ChatRole.MEMBER


class AddMemberHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
        user_repo: AbstractUserRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
        self.user_repo = user_repo
    
    async def handle(self, cmd: AddMemberCommand) -> ChatMember:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        if chat.type in (ChatType.PRIVATE, ChatType.SECRET,):
            raise ForbiddenError("Нельзя добавить участника в данный тип чата")
        
        user = await self.user_repo.get_by_id(cmd.user_id)
        if not user:
            raise NotFoundError("Юзера не существует")
        
        actor = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if not actor:
            raise ForbiddenError("Вы не состоите в этом чате")
        if actor.role not in (ChatRole.OWNER, ChatRole.ADMIN):
            raise ForbiddenError("Недостаточно прав для добавления участников")
        
        existing = await self.chat_member_repo.get_member(cmd.user_id, cmd.chat_id)
        if existing:
            raise AlreadyExistsError("Юзер уже подписан на Чат")
        
        chat_member = ChatMember(
            id=uuid4(),
            chat_id=cmd.chat_id,
            user_id=cmd.user_id,
            role=cmd.role,
            joined_at=datetime.now(UTC),
        )
        
        chat.add_member()
        
        await self.chat_member_repo.save(chat_member)
        await self.chat_repo.save(chat)
        
        return chat_member