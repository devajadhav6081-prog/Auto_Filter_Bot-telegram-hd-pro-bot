import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, CopyTextButton
from Script import script
from info import OWNER_LNK, OWNER_UPI_ID, QR_CODE, SUBSCRIPTION
from database.config_db import mdb
from utils import temp

def _web_app_data_filter(_, __, message):
    return bool(getattr(message, "web_app_data", None))

@Client.on_message(filters.private & filters.incoming & filters.create(_web_app_data_filter))
async def custom_menu_actions(client, message):
    action = (message.web_app_data.data or "").strip().lower()
    if action == "help":
        return await message.reply_text(script.HELP_TXT, parse_mode=enums.ParseMode.HTML)
    if action == "about":
        return await message.reply_text(script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK), parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    if action == "topsearch":
        def is_alphanumeric(value):
            return bool(re.match(r"^[a-zA-Z0-9 ]*$", value))
        top_messages = await mdb.get_top_messages(20)
        seen, items = set(), []
        for item in top_messages:
            lowered = item.lower()
            if lowered not in seen and is_alphanumeric(item):
                seen.add(lowered)
                items.append(item[:32] + "..." if len(item) > 35 else item)
        keyboard = [items[i:i+2] for i in range(0, len(items), 2)]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, placeholder="Most searches of the day") if keyboard else None
        return await message.reply_text("<b>Tᴏᴘ Sᴇᴀʀᴄʜᴇs Oғ Tʜᴇ Dᴀʏ 👇</b>", reply_markup=markup, parse_mode=enums.ParseMode.HTML)
    if action == "premium":
        buttons = [
            [InlineKeyboardButton("📲 ꜱᴇɴᴅ ᴘᴀʏᴍᴇɴᴛ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ", url=OWNER_LNK)],
            [InlineKeyboardButton("UPI ID Copy Karein ??", copy_text=CopyTextButton(text=OWNER_UPI_ID), style=enums.ButtonStyle.PRIMARY)],
            [InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data", style=enums.ButtonStyle.DANGER)]
        ]
        return await message.reply_photo(photo=SUBSCRIPTION, caption=script.PREPLANS_TXT.replace("{}", message.from_user.mention, 1).replace("{}", OWNER_UPI_ID, 1), reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
    await message.reply_text("Please choose an option from the custom menu.")
