from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository


@dataclass
class CreateGroupCommand:
    actor_id: UUID
    title: str
    avatar_url: str | None = None
    is_public: bool = False


class CreateGroupHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
    
    async def handle(self, cmd: CreateGroupCommand) -> Chat:
        group = Chat(
            id=uuid4(),
            type=ChatType.GROUP,
            created_by=cmd.actor_id,
            created_at=datetime.now(UTC),
            title=cmd.title,
            avatar_url=cmd.avatar_url,
            is_public=cmd.is_public
        )
        
        chat_member = ChatMember(
            id=uuid4(),
            chat_id=group.id,
            user_id=cmd.actor_id,
            joined_at=datetime.now(UTC),
            role=ChatRole.OWNER,
        )
        
        group.add_member()
        
        await self.chat_repo.save(group)
        await self.chat_member_repo.save(chat_member)
        
        return group