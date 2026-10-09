import random
import telebot

# توکن ربات شما
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

# آیدی یا یوزرنیم گروه (بدون @)
TARGET_GROUP = "Linkkadde1"

# ساخت شیء ربات
bot = telebot.TeleBot(BOT_TOKEN)

SAMPLE_REPLIES = [
    "حله، موافقم!",
    "جدی؟ بیشتر توضیح بده.",
    "درسته، حق با توئه.",
    "چه جالب، چطور مگه؟",
    "پیامت رو دیدم، چه برنامه‌ای داری براش؟"
]

# تابع دریافت تمام پیام‌های متنی در گروه‌ها
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_all_messages(message):
    # بررسی اینکه پیام در گروه باشد
    if message.chat.type not in ['group', 'supergroup']:
        return

    # بررسی اینکه پیام مربوط به همان گروه هدف باشد (چک کردن یوزرنیم گروه)
    if message.chat.username and message.chat.username.lower() != TARGET_GROUP.lower():
        return

    try:
        # نمایش وضعیت تایپ کردن
        bot.send_chat_action(message.chat.id, 'typing')
    except Exception:
        pass

    # انتخاب پاسخ راندوم
    reply_text = random.choice(SAMPLE_REPLIES)

    # ارسال پاسخ با ریپلای
    bot.reply_to(message, reply_text)

if __name__ == "__main__":
    print("ربات با موفقیت روشن شد و در حال گوش دادن به گروه است...")
    # اجرای مداوم ربات بدون خطای Event Loop
    bot.infinity_none_stop = True
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
