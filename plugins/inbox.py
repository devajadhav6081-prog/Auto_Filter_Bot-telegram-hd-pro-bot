import logging
from datetime import datetime, timezone

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import ADMINS
from database.users_chats_db import db

logger = logging.getLogger(__name__)
inbox_col = db.db.inbox

CLOSED_TEXT = (
    "Owner ne aapka inbox band kar diya hai. "
    "Agar aapko koi aur problem hai to fir se bot se connect karein."
)


@Client.on_message(filters.private & ~filters.user(ADMINS) & ~filters.regex(r"^/"))
async def receive_user_inbox(client, message):
    user = message.from_user
    if not user:
        return

    record = await inbox_col.find_one({"user_id": user.id})
    if not record or record.get("status") != "open":
        await inbox_col.update_one(
            {"user_id": user.id},
            {"$set": {"status": "open", "updated_at": datetime.now(timezone.utc)},
             "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True
        )

    name = (user.first_name or "Unknown").replace("<", "&lt;").replace(">", "&gt;")
    username = f"@{user.username}" if user.username else "Not set"
    header = (
        "<b>📥 NEW INBOX MESSAGE</b>\n\n"
        f"👤 User: {name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔗 Username: {username}\n"
        f"📌 Status: OPEN"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Reply", callback_data=f"inbox_reply_{user.id}"),
         InlineKeyboardButton("🔒 Close Inbox", callback_data=f"inbox_close_{user.id}")]
    ])

    for admin_id in ADMINS:
        try:
            await client.send_message(admin_id, header, reply_markup=keyboard)
            await client.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.id
            )
        except Exception as e:
            logger.warning("Could not deliver inbox message to admin %s: %s", admin_id, e)


@Client.on_callback_query(filters.regex(r"^inbox_(reply|close)_([0-9]+)$") & filters.user(ADMINS))
async def inbox_actions(client, query):
    action, user_id = query.matches[0].group(1), int(query.matches[0].group(2))
    if action == "reply":
        await query.answer("Reply ke liye /reply USER_ID MESSAGE bhejein.", show_alert=True)
        return await query.message.reply_text(
            f"Reply format: <code>/reply {user_id} Aapka message</code>"
        )

    result = await inbox_col.update_one(
        {"user_id": user_id, "status": "open"},
        {"$set": {"status": "closed", "closed_at": datetime.now(timezone.utc),
                  "closed_by": query.from_user.id}}
    )
    if not result.modified_count:
        return await query.answer("Ye inbox pehle se close hai.", show_alert=True)

    try:
        await client.send_message(user_id, CLOSED_TEXT)
    except Exception as e:
        logger.warning("Could not send inbox-closed notice to %s: %s", user_id, e)

    await query.message.edit_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton("✅ Inbox Closed", callback_data="inbox_closed")]])
    )
    await query.answer("Inbox closed; user ko notification bhej diya.")


@Client.on_callback_query(filters.regex(r"^inbox_closed$") & filters.user(ADMINS))
async def inbox_closed_notice(client, query):
    await query.answer("This inbox is closed.", show_alert=True)


@Client.on_message(filters.private & filters.command("reply") & filters.user(ADMINS))
async def reply_to_inbox_user(client, message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /reply USER_ID Your message")
    try:
        user_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid user ID.")
    record = await inbox_col.find_one({"user_id": user_id})
    if not record or record.get("status") != "open":
        return await message.reply_text("Ye inbox open nahi hai. User ko reply nahi bheja gaya.")
    reply_text = message.text.split(maxsplit=2)[2]
    try:
        await client.send_message(user_id, reply_text)
        await message.reply_text("✅ Reply user ko bhej diya.")
    except Exception as e:
        logger.exception("Inbox reply failed")
        await message.reply_text(f"Reply send nahi hua: <code>{e}</code>")
