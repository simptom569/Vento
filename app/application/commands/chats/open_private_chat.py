from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime, UTC

from app.domain.entities.chat import Chat, ChatMember
from app.domain.entities.enums import ChatRole, ChatType
from app.domain.ports.repositories.chat_repo import AbstractChatRepository
from app.domain.ports.repositories.chat_member_repo import AbstractChatMemberRepository
from app.domain.ports.repositories.user_repo import AbstractUserRepository
from app.domain.exceptions import NotFoundError


@dataclass
class OpenPrivateChatCommand:
    actor_id: UUID
    user_id: UUID


class OpenPrivateChatHandler:
    def __init__(
        self,
        chat_repo: AbstractChatRepository,
        chat_member_repo: AbstractChatMemberRepository,
        user_repo: AbstractUserRepository,
    ):
        self.chat_repo = chat_repo
        self.chat_member_repo = chat_member_repo
        self.user_repo = user_repo

    async def handle(self, cmd: OpenPrivateChatCommand) -> Chat:
        user = await self.user_repo.get_by_id(cmd.user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        chat = await self.chat_repo.get_private_chat_including_deleted(cmd.actor_id, cmd.user_id)

        if chat:
            member = await self.chat_member_repo.get_member_including_deleted(cmd.actor_id, chat.id)
            if member and member.deleted_at:
                member.restore()
                await self.chat_member_repo.save(member)
            return chat

        chat = Chat(
            id=uuid4(),
            type=ChatType.PRIVATE,
            created_by=cmd.actor_id,
            created_at=datetime.now(UTC),
        )

        await self.chat_repo.save(chat)

        for user_id in (cmd.actor_id, cmd.user_id):
            chat_member = ChatMember(
                id=uuid4(),
                chat_id=chat.id,
                user_id=user_id,
                joined_at=datetime.now(UTC),
                role=ChatRole.MEMBER,
            )
            chat.add_member()
            await self.chat_member_repo.save(chat_member)

        await self.chat_repo.save(chat)

        return chat