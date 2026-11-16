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
async def clear_left_member_request(client, update):
    if update.chat.id not in AUTH_REQ_CHANNELS:
        return

    new_status = update.new_chat_member.status
    if new_status in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED):
        user_id = update.new_chat_member.user.id
        await db.remove_join_req(user_id, update.chat.id)
