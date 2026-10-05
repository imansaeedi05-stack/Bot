import os
import logging
from flask import Flask
import threading
from pyrogram import Client, filters

app = Flask("")

@app.route("/")
def home():
    return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

logging.basicConfig(level=logging.INFO)

# توکن جدید شما
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"

bot = Client("test_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("✅ ربات با موفقیت تست شد و پاسخ می‌دهد!")

if __name__ == "__main__":
    bot.run()
