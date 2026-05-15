from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.application.commands.chats.create_group import CreateGroupCommand, CreateGroupHandler
from app.application.commands.chats.create_channel import CreateChannelCommand, CreateChannelHandler
from app.application.commands.chats.open_private_chat import OpenPrivateChatCommand, OpenPrivateChatHandler
from app.application.commands.chats.delete_chat import DeleteChatCommand, DeleteChatHandler
from app.application.commands.chats.update_group import UpdateGroupCommand, UpdateGroupHandler
from app.application.commands.chats.update_channel import UpdateChannelCommand, UpdateChannelHandler
from app.application.commands.chats.mute_chat import MuteChatCommand, MuteChatHandler
from app.application.commands.chats.join_chat import JoinChatCommand, JoinChatHandler
from app.application.commands.chats.leave_chat import LeaveChatCommand, LeaveChatHandler
from app.application.commands.chats.add_member import AddMemberCommand, AddMemberHandler
from app.application.commands.chats.remove_member import RemoveMemberCommand, RemoveMemberHandler
from app.application.commands.chats.change_member_role import ChangeMemberRoleCommand, ChangeMemberRoleHandler
from app.application.queries.chats.get_user_chats import GetUserChatsQuery, GetUserChatsHandler
from app.application.queries.chats.get_chat import GetChatQuery, GetChatHandler
from app.application.queries.chats.get_chat_members import GetChatMembersQuery, GetChatMembersHandler
from app.domain.exceptions import AlreadyExistsError, ForbiddenError, NotFoundError
from app.core.dependencies import CurrentUser
from app.presentation.schemas.chat import (
    GroupRequest, GroupResponse,
    ChannelRequest, ChannelResponse,
    PrivateRequest, PrivateResponse,
    ChatListItemResponse,
    ChatResponse,
    DeleteChatRequest,
    UpdateGroupRequest,
    UpdateChannelRequest,
    MuteChatRequest,
    AddMemberRequest, AddMemberResponse,
    ChangeMemberRequest, ChangeMemberResponse,
    ChatMemberListItemResponse,
)


router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatListItemResponse], status_code=200)
@inject
async def get_user_chats(
    current_user: CurrentUser,
    handler: FromDishka[GetUserChatsHandler],
):
    query = GetUserChatsQuery(
        actor_id=current_user.id,
    )
    chats = await handler.handle(query)
    return [ChatListItemResponse.from_domain(c) for c in chats]


@router.post("/group", response_model=GroupResponse, status_code=201)
@inject
async def create_group(
    body: GroupRequest,
    current_user: CurrentUser,
    handler: FromDishka[CreateGroupHandler],
):
    cmd = CreateGroupCommand(
        actor_id=current_user.id,
        title=body.title,
        avatar_url=body.avatar_url,
        is_public=body.is_public,
    )
    chat = await handler.handle(cmd)
    return GroupResponse.from_domain(chat)


@router.post("/channel", response_model=ChannelResponse, status_code=201)
@inject
async def create_channel(
    body: ChannelRequest,
    current_user: CurrentUser,
    handler: FromDishka[CreateChannelHandler],
):
    try:
        cmd = CreateChannelCommand(
            actor_id=current_user.id,
            title=body.title,
            username=body.username,
            avatar_url=body.avatar_url,
            is_public=body.is_public,
        )
        chat = await handler.handle(cmd)
        return ChannelResponse.from_domain(chat)
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/private", response_model=PrivateResponse, status_code=200)
@inject
async def open_private_chat(
    body: PrivateRequest,
    current_user: CurrentUser,
    handler: FromDishka[OpenPrivateChatHandler],
):
    try:
        cmd = OpenPrivateChatCommand(
            actor_id=current_user.id,
            user_id=body.user_id,
        )
        chat = await handler.handle(cmd)
        return PrivateResponse.from_domain(chat)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{chat_id}/group", status_code=200)
@inject
async def update_group(
    chat_id: UUID,
    body: UpdateGroupRequest,
    current_user: CurrentUser,
    handler: FromDishka[UpdateGroupHandler],
):
    try:
        cmd = UpdateGroupCommand(
            actor_id=current_user.id,
            chat_id=chat_id,
            title=body.title,
            avatar_url=body.avatar_url,
        )
        await handler.handle(cmd)
        return {"message": "Group updated successfully"}
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{chat_id}/channel", status_code=200)
@inject
async def update_channel(
    chat_id: UUID,
    body: UpdateChannelRequest,
    current_user: CurrentUser,
    handler: FromDishka[UpdateChannelHandler],
):
    try:
        cmd = UpdateChannelCommand(
            actor_id=current_user.id,
            chat_id=chat_id,
            title=body.title,
            username=body.username,
            is_public=body.is_public,
            avatar_url=body.avatar_url,
            discussion_chat_id=body.discussion_chat_id,
        )
        await handler.handle(cmd)
        return {"message": "Channel updated successfully"}
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{chat_id}/mute", status_code=204)
@inject
async def mute_chat(
    chat_id: UUID,
    body: MuteChatRequest,
    current_user: CurrentUser,
    handler: FromDishka[MuteChatHandler],
):
    try:
        cmd = MuteChatCommand(
            actor_id=current_user.id,
            chat_id=chat_id,
            time=body.time,
        )
        await handler.handle(cmd)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{chat_id}/join", status_code=204)
@inject
async def join_chat(
    chat_id: UUID,
    current_user: CurrentUser,
    handler: FromDishka[JoinChatHandler],
):
    try:
        cmd = JoinChatCommand(
            actor_id=current_user.id,
            chat_id=chat_id,
        )
        await handler.handle(cmd)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{chat_id}/leave", status_code=204)
@inject
async def leave_chat(
    chat_id: UUID,
    current_user: CurrentUser,
    handler: FromDishka[LeaveChatHandler],
):
    try:
        cmd = LeaveChatCommand(
            actor_id=current_user.id,
            chat_id=chat_id,
        )
        await handler.handle(cmd)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{chat_id}/members", response_model=AddMemberResponse, status_code=201)
@inject
async def add_member(
    chat_id: UUID,
    body: AddMemberRequest,
    current_user: CurrentUser,
    handler: FromDishka[AddMemberHandler],
):
    try:
        cmd = AddMemberCommand(
            user_id=body.user_id,
            chat_id=chat_id,
            actor_id=current_user.id,
            role=body.role,
        )
        chat_member = await handler.handle(cmd)
        return AddMemberResponse.from_domain(chat_member)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{chat_id}/members/{user_id}", status_code=204)
@inject
async def remove_member(
    chat_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    handler: FromDishka[RemoveMemberHandler],
):
    try:
        cmd = RemoveMemberCommand(
            chat_id=chat_id,
            actor_id=current_user.id,
            user_id=user_id,
        )
        await handler.handle(cmd)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{chat_id}/members/{user_id}", response_model=ChangeMemberResponse, status_code=200)
@inject
async def change_member(
    chat_id: UUID,
    user_id: UUID,
    body: ChangeMemberRequest,
    current_user: CurrentUser,
    handler: FromDishka[ChangeMemberRoleHandler],
):
    try:
        cmd = ChangeMemberRoleCommand(
            user_id=user_id,
            chat_id=chat_id,
            actor_id=current_user.id,
            role=body.role,
        )
        chat_member = await handler.handle(cmd)
        return ChangeMemberResponse.from_domain(chat_member)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{chat_id}/members", response_model=list[ChatMemberListItemResponse], status_code=200)
@inject
async def get_chat_members(
    chat_id: UUID,
    current_user: CurrentUser,
    handler: FromDishka[GetChatMembersHandler],
):
    try:
        query = GetChatMembersQuery(
            actor_id=current_user.id,
            chat_id=chat_id,
        )
        chat_members = await handler.handle(query)
        return [ChatMemberListItemResponse.from_domain(c) for c in chat_members]
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{chat_id}", response_model=ChatResponse, status_code=200)
@inject
async def get_chat(
    chat_id: UUID,
    current_user: CurrentUser,
    handler: FromDishka[GetChatHandler],
):
    try:
        query = GetChatQuery(
            actor_id=current_user.id,
            chat_id=chat_id,
        )
        chat = await handler.handle(query)
        return ChatResponse.from_domain(chat)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{chat_id}", status_code=204)
@inject
async def delete_chat(
    chat_id: UUID,
    body: DeleteChatRequest,
    current_user: CurrentUser,
    handler: FromDishka[DeleteChatHandler],
):
    try:
        cmd = DeleteChatCommand(
            actor_id=current_user.id,
            chat_id=chat_id,
            delete_for_everyone=body.deleted_for_everyone,
        )
        await handler.handle(cmd)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))