#Join Telegram Channel - @DREAMXBOTZ

from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS, AUTH_REQ_CHANNELS
from pyrogram.filters import create

def is_auth_req_channel(_, __, update):
    return update.chat.id in AUTH_REQ_CHANNELS

@Client.on_chat_join_request(create(is_auth_req_channel))
async def join_reqs(client, message: ChatJoinRequest):
    await db.add_join_req(message.from_user.id, message.chat.id)


@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")

from pyrogram import enums

@Client.on_chat_member_updated()
async def clear_member_request(client, update):
    # Remove the pending-request record as soon as the request is approved
    # or the user leaves/is removed. This prevents an old request from
    # hiding the Request to Join button after the user leaves later.
    if int(update.chat.id) not in AUTH_REQ_CHANNELS:
        return

    member = update.new_chat_member
    if not member:
        return

    status = member.status
    if status in (
        enums.ChatMemberStatus.MEMBER,
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
        enums.ChatMemberStatus.LEFT,
        enums.ChatMemberStatus.BANNED,
    ):
        await db.remove_join_req(member.user.id, int(update.chat.id))
