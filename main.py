import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters

# راه‌اندازی Flask برای پاسخ به پورت رندر
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is alive and running!"


def run_flask():
  app.run(host="0.0.0.0", port=10000)


# تنظیمات کلاینت پیروگرام (با مقادیر متغیرهای محیطی)
# API_ID, API_HASH, BOT_TOKEN را از تنظیمات Render می‌‌خواند
import os

app_bot = Client(
    "my_bot",
    api_id=int(os.environ.get("API_ID", 0)),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", ""),
)


@app_bot.on_message(filters.command("start"))
async def start_cmd(client, message):
  await message.reply_text("سلام! ربات با موفقیت روی رندر روشن شد 🚀")


if __name__ == "__main__":
  # اجرای Flask در پس‌زمینه برای اینکه پورت رندر اشغال نشود و ارور ندهد
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # اجرای ربات پیروگرام
  print("Starting Pyrogram Bot...")
  app_bot.run()
