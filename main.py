import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters

# اطلاعات اکانت و ربات شما
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8610788849:AAFu-oLDMAyFNUYN8RRi6oRM7XeHJ58q-Fs"
ADMIN_ID = 7165683193

# راه‌اندازی Flask برای پاسخ به پورت رندر و جلوگیری از ارور
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is alive and running!"


def run_flask():
  app.run(host="0.0.0.0", port=10000)


# راه‌اندازی کلاینت پیروگرام با مقادیر مستقیماً وارد شده
app_bot = Client(
    "my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
)


@app_bot.on_message(filters.command("start"))
async def start_cmd(client, message):
  await message.reply_text("سلام! ربات با موفقیت روی رندر روشن شد 🚀")


if __name__ == "__main__":
  # اجرای Flask در پس‌زمینه برای باز نگه داشتن پورت سرویس
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  # اجرای ربات پیروگرام
  print("Starting Pyrogram Bot...")
  app_bot.run()
