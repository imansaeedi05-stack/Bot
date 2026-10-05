import os
import logging
from flask import Flask
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

app = Flask("")

@app.route("/")
def home():
    return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"

bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ افزودن اکانت", callback_data="menu_add"),
            InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data="menu_list"),
        ],
        [
            InlineKeyboardButton("🗑 حذف اکانت", callback_data="menu_del"),
            InlineKeyboardButton("🔄 بازخوانی سشن‌ها", callback_data="menu_reload"),
        ],
    ])

    await message.reply_text(
        "🤖 **پنل مدیریت پیشرفته اکانت‌های ویس‌چت**\n\n"
        "از دکمه‌های شیشه‌ای زیر برای مدیریت سریع ربات استفاده کنید:",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex(r"^menu_"))
async def callback_menu(client, callback_query):
    data = callback_query.data
    if data == "menu_add":
        await callback_query.message.edit_text("📱 بخش افزودن اکانت به زودی اضافه می‌شود.")
    elif data == "menu_list":
        await callback_query.answer("❌ هیچ اکانتی فعال نیست.", show_alert=True)
    elif data == "menu_del":
        await callback_query.answer("❌ هیچ اکانتی برای حذف وجود ندارد.", show_alert=True)
    elif data == "menu_reload":
        await callback_query.answer("✅ بازخوانی شد.", show_alert=True)

if __name__ == "__main__":
    bot.run()
