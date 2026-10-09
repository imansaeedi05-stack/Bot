import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message

# اطلاعاتی که فرستادید
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

# لینک گروه مورد نظر
TARGET_GROUP = "Linkkadde1"

# ساخت کلاینت ربات با توکن رسمی
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# لیست پاسخ‌های نمونه (می‌توانید تغییر دهید)
SAMPLE_REPLIES = [
    "حله، موافقم!",
    "جدی؟ بیشتر توضیح بده.",
    "درسته، حق با توئه.",
    "چه جالب، چطور مگه؟",
    "پیامت رو دیدم، چه برنامه‌ای داری براش؟"
]

@app.on_message(filters.chat(TARGET_GROUP) & ~filters.bot)
async def chat_in_group(client: Client, message: Message):
    # بررسی اینکه پیام متن داشته باشد
    if not message.text:
        return

    # تاخیر کوتاه برای طبیعی‌تر شدن پاسخ‌دهی (بین ۲ تا ۴ ثانیه)
    await asyncio.sleep(random.uniform(2.0, 4.0))

    try:
        await client.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass
    
    await asyncio.sleep(1.5)

    # انتخاب پاسخ راندوم
    reply_text = random.choice(SAMPLE_REPLIES)

    # ارسال پاسخ با ریپلای به پیام ممبر
    await message.reply_text(reply_text, quote=True)

print("ربات با موفقیت روشن شد و در حال گوش دادن به گروه است...")
app.run()
