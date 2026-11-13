import logging

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import ADMINS
from database.users_chats_db import db

logger = logging.getLogger(__name__)

PAGE_SIZE = 10


def _admin_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users Management", callback_data="admin_users_0")],
        [
            InlineKeyboardButton("📊 Bot Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("💎 Premium Users", callback_data="admin_premium"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_command_broadcast"),
            InlineKeyboardButton("👥 Group Broadcast", callback_data="admin_command_grp_broadcast"),
        ],
        [
            InlineKeyboardButton("🚫 Ban / Unban", callback_data="admin_command_ban"),
            InlineKeyboardButton("🔄 Restart", callback_data="admin_command_restart"),
        ],
    ])


@Client.on_message(filters.private & filters.command("admin") & filters.user(ADMINS))
async def admin_panel(client, message):
    total_users = await db.total_users_count()
    total_groups = await db.total_chat_count()
    text = (
        "<b>⚙️ ADMIN CONTROL PANEL</b>\n\n"
        f"👥 Registered Users: <code>{total_users}</code>\n"
        f"👨‍👩‍👧‍👦 Connected Groups: <code>{total_groups}</code>\n\n"
        "Choose an option below:"
    )
    await message.reply_text(text, reply_markup=_admin_markup())


@Client.on_callback_query(filters.regex(r"^admin_(stats|users_\\d+|premium|command_.*)$") & filters.user(ADMINS))
async def admin_panel_callbacks(client, query):
    data = query.data

    if data == "admin_stats":
        total_users = await db.total_users_count()
        total_groups = await db.total_chat_count()
        banned_users = await db.col.count_documents({"ban_status.is_banned": True})
        premium_users = await db.users.count_documents({})
        return await query.message.edit_text(
            "<b>📊 BOT STATISTICS</b>\n\n"
            f"👥 Total Users: <code>{total_users}</code>\n"
            f"👨‍👩‍👧‍👦 Total Groups: <code>{total_groups}</code>\n"
            f"🚫 Banned Users: <code>{banned_users}</code>\n"
            f"💎 Premium Records: <code>{premium_users}</code>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]])
        )

    if data == "admin_back":
        total_users = await db.total_users_count()
        total_groups = await db.total_chat_count()
        return await query.message.edit_text(
            "<b>⚙️ ADMIN CONTROL PANEL</b>\n\n"
            f"👥 Registered Users: <code>{total_users}</code>\n"
            f"👨‍👩‍👧‍👦 Connected Groups: <code>{total_groups}</code>\n\n"
            "Choose an option below:",
            reply_markup=_admin_markup()
        )

    if data == "admin_premium":
        count = await db.users.count_documents({})
        return await query.message.edit_text(
            f"<b>💎 PREMIUM USERS</b>\n\nTotal premium records: <code>{count}</code>\n"
            "Use /premium_users to view the existing premium-user list (if enabled in this bot).",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]])
        )

    if data.startswith("admin_command_"):
        command = data.replace("admin_command_", "", 1)
        return await query.answer(f"Use /{command} in this chat.", show_alert=True)

    if data.startswith("admin_users_"):
        page = int(data.rsplit("_", 1)[1])
        total = await db.total_users_count()
        cursor = db.col.find({}).sort("id", 1).skip(page * PAGE_SIZE).limit(PAGE_SIZE)
        users = [user async for user in cursor]

        if not users:
            return await query.answer("No registered users found.", show_alert=True)

        lines = [f"<b>👥 USERS MANAGEMENT</b>\nTotal registered: <code>{total}</code>\n"]
        for user in users:
            user_id = user.get("id", 0)
            name = user.get("name") or "Unknown"
            banned = user.get("ban_status", {}).get("is_banned", False)
            premium = bool(await db.get_user(user_id))
            lines.append(
                f"\n<b>{name}</b>\n"
                f"🆔 <code>{user_id}</code>\n"
                f"💎 Premium: {'Yes' if premium else 'No'} | "
                f"🚫 Banned: {'Yes' if banned else 'No'}"
            )

        buttons = []
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_users_{page - 1}"))
        if (page + 1) * PAGE_SIZE < total:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"admin_users_{page + 1}"))
        if nav:
            buttons.append(nav)
        buttons.append([InlineKeyboardButton("⬅️ Admin Panel", callback_data="admin_back")])
        await query.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup(buttons))
        return await query.answer()

    await query.answer()
