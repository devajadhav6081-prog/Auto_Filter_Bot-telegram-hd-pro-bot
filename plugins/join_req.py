#Join Telegram Channel - @DREAMXBOTZ

from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import ADMINS, AUTH_REQ_CHANNELS
from pyrogram.filters import create

def is_auth_req_channel(_, __, update):
    return update.chat.id in AUTH_REQ_CHANNELS

@Client.on_chat_join_request(create(is_auth_req_channel))
async def join_reqs(client, message: ChatJoinRequest):
    await db.add_join_req(message.from_user.id, message.chat.id)

@Client.on_chat_member_updated(create(is_auth_req_channel))
async def force_sub_member_updates(client, update):
    # A pending request is no longer valid after the user leaves or is removed.
    new_member = update.new_chat_member
    if new_member and new_member.status in (
        enums.ChatMemberStatus.LEFT,
        enums.ChatMemberStatus.BANNED,
    ):
        await db.del_join_req(new_member.user.id, update.chat.id)



@Client.on_message(filters.command("delreq") & filters.private & filters.user(ADMINS))
async def del_requests(client, message):
    await db.del_join_req()    
    await message.reply("<b>⚙ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ᴄʜᴀɴɴᴇʟ ʟᴇғᴛ ᴜꜱᴇʀꜱ ᴅᴇʟᴇᴛᴇᴅ</b>")
