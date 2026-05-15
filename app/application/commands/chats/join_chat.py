from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.domain.entities.chat import ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.exceptions import AlreadyExistsError, NotFoundError, ForbiddenError


@dataclass
class JoinChatCommand:
    actor_id: UUID
    chat_id: UUID


class JoinChatHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: JoinChatCommand) -> ChatMember:
        chat = await self.chat_repo.get_by_id(cmd.chat_id)
        if not chat:
            raise NotFoundError("Чата не существует")
        
        if chat.type in (ChatType.PRIVATE, ChatType.SECRET,):
            raise ForbiddenError("Нельзя присоедениться к данному типу чата")
        
        if not chat.is_public:
            raise ForbiddenError("Чат является приватным")
        
        existing = await self.chat_member_repo.get_member(cmd.actor_id, cmd.chat_id)
        if existing:
            raise AlreadyExistsError("Вы уже подписаны на данный Чат")
        
        chat_member = ChatMember(
            id=uuid4(),
            chat_id=cmd.chat_id,
            user_id=cmd.actor_id,
            joined_at=datetime.now(UTC),
            role=ChatRole.SUBSCRIBER,
        )
        
        chat.add_member()
        
        await self.chat_repo.save(chat)
        await self.chat_member_repo.save(chat_member)
        
        return chat_member