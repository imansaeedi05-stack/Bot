import asyncio
import logging
import os
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

app = Flask("")

@app.route("/")
def home():
    return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8713081155:AAE0SPxswRAW3y2TK98HM65D4c9Hc7ipMzs"
OWNER_ID = 7165683193

# استفاده از نام متمرکز و مستقل برای سشن ربات
bot = Client("bot_main_instance", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# این بخش تمام پیام‌های ورودی را در لاگ رندر ثبت می‌کند تا ببینیم آیا پیامی دریافت می‌شود یا خیر
@bot.on_message(group=-1)
async def debug_all_messages(client, message: Message):
    user_id = message.from_user.id if message.from_user else "Unknown"
    text = message.text or "Non-text message"
    logger.info(f"==> DEBUG: Received message from user {user_id}: {text}")

@bot.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(client, message: Message):
    logger.info("Command /start executed successfully by owner.")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 ورود به کانال A_ToolsX", url="https://t.me/A_ToolsX")]
    ])
    await message.reply_text(
        "🤖 **پنل مدیریت ربات فعال است!**\n\nتوسعه یافته و آماده کار.",
        reply_markup=keyboard
    )

async def main():
    logger.info("Initializing bot connection...")
    await bot.start()
    logger.info("Bot is now running and listening for updates!")
    await idle()
    logger.info("Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
