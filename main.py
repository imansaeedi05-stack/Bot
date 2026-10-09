import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message

# اطلاعات شما
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

# لینک گروه مورد نظر
TARGET_GROUP = "Linkkadde1"

# ساخت کلاینت ربات
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

SAMPLE_REPLIES = [
    "حله، موافقم!",
    "جدی؟ بیشتر توضیح بده.",
    "درسته، حق با توئه.",
    "چه جالب، چطور مگه؟",
    "پیامت رو دیدم، چه برنامه‌ای داری براش؟"
]

@app.on_message(filters.chat(TARGET_GROUP) & ~filters.bot)
async def chat_in_group(client: Client, message: Message):
    if not message.text:
        return

    await asyncio.sleep(random.uniform(2.0, 4.0))

    try:
        await client.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass
    
    await asyncio.sleep(1.5)
    reply_text = random.choice(SAMPLE_REPLIES)
    await message.reply_text(reply_text, quote=True)

if __name__ == "__main__":
    print("ربات در حال راه‌اندازی...")
    # راه‌اندازی ایمن حلقه رویداد برای جلوگیری از خطای پایتون جدید
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    app.run()
