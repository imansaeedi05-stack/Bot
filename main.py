import os
import threading
from flask import Flask
from pyrogram import Client, filters
import telebot

# اطلاعات حساب و ربات شما
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8610788849:AAFu-oLDMAyFNUYN8RRi6oRM7XeHJ58q-Fs"

# راه‌‌‌‌اندازی ربات با telebot برای پاسخگویی سریع و تضمینی به دستورات و دکمه‌ها
bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = telebot.types.InlineKeyboardMarkup()
  btn = telebot.types.InlineKeyboardButton(
      "📢 ورود به کانال", url="https://t.me/feel_your_touch"
  )
  markup.add(btn)
  bot.reply_to(
      message,
      "🤖 **پنل مدیریت پیشرفته اکانت‌های ویس‌چت**\n\nسلام! ربات با موفقیت فعال شد و آماده‌ی کار است.",
      reply_markup=markup,
      parse_mode="Markdown",
  )


def run_bot():
  # اجرای لوپ ربات تلگرام به صورت ایمن و بدون توقف
  bot.infinity_polling(skip_pending=True)


# راه‌اندازی پیروگرام برای کارهای مرتبط با اکانت‌ها و ویس‌چت
app = Client(
    "bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
)


@app.on_message(filters.command("ping"))
async def ping_handler(client, message):
  await message.reply("پیروگرام هم آنلاین و متصل است!")


# راه‌اندازی یک سرور وب ساده با فلاسک برای ماندن در دسترس روی رندر (پورت 10000)
server = Flask(__name__)


@server.route("/")
def home():
  return "Bot is running and alive!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  server.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  # اجرای وب‌سرویس در یک ترد جداگانه
  t_flask = threading.Thread(target=run_flask)
  t_flask.daemon = True
  t_flask.start()

  # اجرای ترد ربات تلگرام برای پاسخگویی به استارت
  t_bot = threading.Thread(target=run_bot)
  t_bot.daemon = True
  t_bot.start()

  print("تمامی سرویس‌ها با موفقیت استارت شدند...")

  # اجرای پیروگرام به عنوان فرآیند اصلی نگهدارنده برنامه
  app.run()
