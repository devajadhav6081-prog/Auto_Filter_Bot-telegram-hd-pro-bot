import logging

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import (
    ADMINS, Bot_cmds, MAINTENANCE, PM_SEARCH, AUTO_FFILTER, AUTO_DELETE,
    IMDB, TMDB_POSTER, STREAM_MODE, PREMIUM_STREAM_MODE, SPELL_CHECK_REPLY,
    USE_CAPTION_FILTER, PROTECT_CONTENT
)
from database.users_chats_db import db

logger = logging.getLogger(__name__)
PAGE_SIZE = 10


def _admin_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users Management", callback_data="admin_users_0")],
        [
            InlineKeyboardButton("📚 Commands", callback_data="admin_commands"),
            InlineKeyboardButton("⚙️ System Settings", callback_data="admin_system"),
        ],
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


def _back_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]
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


@Client.on_callback_query(
    filters.regex(r"^admin_(stats|users_[0-9]+|premium|commands|system|back|command_.*)$")
    & filters.user(ADMINS)
)
async def admin_panel_callbacks(client, query):
    data = query.data

    if data == "admin_commands":
        rows = ["<b>📚 BOT COMMANDS</b>\n"]
        for command, description in Bot_cmds.items():
            safe_description = (
                str(description).replace("&", "&amp;")
                .replace("<", "&lt;").replace(">", "&gt;")
            )
            rows.append(f"/{command} — {safe_description}")
        return await query.message.edit_text("\n".join(rows), reply_markup=_back_markup())

    if data == "admin_system":
        def status(value):
            return "ON ✅" if value else "OFF ❌"

        settings_text = (
            "<b>⚙️ SYSTEM SETTINGS</b>\n\n"
            f"Maintenance: <b>{status(MAINTENANCE)}</b>\n"
            f"PM Search: <b>{status(PM_SEARCH)}</b>\n"
            f"Auto Filter: <b>{status(AUTO_FFILTER)}</b>\n"
            f"Auto Delete: <b>{status(AUTO_DELETE)}</b>\n"
            f"IMDB: <b>{status(IMDB)}</b>\n"
            f"TMDB Poster: <b>{status(TMDB_POSTER)}</b>\n"
            f"Stream Mode: <b>{status(STREAM_MODE)}</b>\n"
            f"Premium Stream: <b>{status(PREMIUM_STREAM_MODE)}</b>\n"
            f"Spell Check: <b>{status(SPELL_CHECK_REPLY)}</b>\n"
            f"Caption Filter: <b>{status(USE_CAPTION_FILTER)}</b>\n"
            f"Protect Content: <b>{status(PROTECT_CONTENT)}</b>\n\n"
            "<i>Ye current runtime configuration hai; yahan se values change nahi hoti.</i>"
        )
        return await query.message.edit_text(settings_text, reply_markup=_back_markup())

    if data == "admin_stats":
        total_users = await db.total_users_count()
        total_groups = await db.total_chat_count()
        banned_users = await db.col.count_documents({"ban_status.is_banned": True})
        premium_users = await db.users.count_documents({})
        stats_text = (
            "<b>📊 BOT STATISTICS</b>\n\n"
            f"👥 Total Users: <code>{total_users}</code>\n"
            f"👨‍👩‍👧‍👦 Total Groups: <code>{total_groups}</code>\n"
            f"🚫 Banned Users: <code>{banned_users}</code>\n"
            f"💎 Premium Records: <code>{premium_users}</code>"
        )
        return await query.message.edit_text(stats_text, reply_markup=_back_markup())

    if data == "admin_back":
        total_users = await db.total_users_count()
        total_groups = await db.total_chat_count()
        text = (
            "<b>⚙️ ADMIN CONTROL PANEL</b>\n\n"
            f"👥 Registered Users: <code>{total_users}</code>\n"
            f"👨‍👩‍👧‍👦 Connected Groups: <code>{total_groups}</code>\n\n"
            "Choose an option below:"
        )
        return await query.message.edit_text(text, reply_markup=_admin_markup())

    if data == "admin_premium":
        count = await db.users.count_documents({})
        text = (
            "<b>💎 PREMIUM USERS</b>\n\n"
            f"Total premium records: <code>{count}</code>\n"
            "Use /premium_users to view the existing premium-user list (if enabled in this bot)."
        )
        return await query.message.edit_text(text, reply_markup=_back_markup())

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

        lines = [
            f"<b>👥 USERS MANAGEMENT</b>\nTotal registered: <code>{total}</code>\n"
        ]
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
