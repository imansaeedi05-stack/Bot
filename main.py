import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# اطلاعات ربات شما
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"
TARGET_GROUP = "Linkkadde1"

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

SAMPLE_REPLIES = [
    "حله، موافقم!",
    "جدی؟ بیشتر توضیح بده.",
    "درسته، حق با توئه.",
    "چه جالب، چطور مگه؟",
    "پیامت رو دیدم، چه برنامه‌ای داری براش؟"
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat = message.chat
    if chat.username and chat.username.lower() != TARGET_GROUP.lower():
        return

    try:
        await context.bot.send_chat_action(chat_id=chat.id, action="typing")
    except Exception:
        pass

    reply_text = random.choice(SAMPLE_REPLIES)
    await message.reply_text(reply_text, quote=True)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    chat_filter = filters.Chat(username=TARGET_GROUP) & filters.TEXT & ~filters.COMMAND
    application.add_handler(MessageHandler(chat_filter, handle_message))

    print("ربات با موفقیت روشن شد و آماده به کار است...")
    application.run_polling()

if __name__ == "__main__":
    main()
