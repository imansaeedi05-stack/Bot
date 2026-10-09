import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message

# اطلاعات مشترک API (می‌توانید برای هر اکانت از API_ID و API_HASH خودشان استفاده کنید، 
# یا برای هر ۴ اکانت از یک API_ID/API_HASH ثبت‌نام شده در my.telegram.org استفاده کنید)
API_ID = 12345678  
API_HASH = "your_api_hash_here"

# لینک گروه مورد نظر
TARGET_GROUP = "Linkkadde1"

# لیست پاسخ‌های نمونه برای چرخش بین اکانت‌ها
SAMPLE_REPLIES = [
    "حله، موافقم!",
    "جدی؟ بیشتر توضیح بده.",
    "درسته، حق با توئه.",
    "چه جالب، چطور مگه؟",
    "پیامت رو دیدم، چه برنامه‌ای داری براش؟"
]

# ساخت ۴ کلاینت مجزا برای ۴ اکانت مختلف با نام‌های session متفاوت
acc1 = Client("account_1", api_id=API_ID, api_hash=API_HASH)
acc2 = Client("account_2", api_id=API_ID, api_hash=API_HASH)
acc3 = Client("account_3", api_id=API_ID, api_hash=API_HASH)
acc4 = Client("account_4", api_id=API_ID, api_hash=API_HASH)

clients = [acc1, acc2, acc3, acc4]

# تابع عمومی برای پاسخ‌دهی هر اکانت
async def handle_message(client, message):
    if not message.text:
        return

    # تاخیر تصادفی تا اکانت‌ها هم‌زمان و ربات‌گونه پیام ندهند
    await asyncio.sleep(random.uniform(4.0, 8.0))

    try:
        await client.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass
    
    await asyncio.sleep(2)
    reply_text = random.choice(SAMPLE_REPLIES)
    await message.reply_text(reply_text, quote=True)

# ثبت رویداد برای تک‌تک اکانت‌ها در گروه مشخص شده
@acc1.on_message(filters.chat(TARGET_GROUP) & ~filters.me & ~filters.bot)
async def acc1_chat(client, message):
    await handle_message(client, message)

@acc2.on_message(filters.chat(TARGET_GROUP) & ~filters.me & ~filters.bot)
async def acc2_chat(client, message):
    await handle_message(client, message)

@acc3.on_message(filters.chat(TARGET_GROUP) & ~filters.me & ~filters.bot)
async def acc3_chat(client, message):
    await handle_message(client, message)

@acc4.on_message(filters.chat(TARGET_GROUP) & ~filters.me & ~filters.bot)
async def acc4_chat(client, message):
    await handle_message(client, message)

async def main():
    # شروع به کار هم‌زمان هر ۴ اکانت
    print("در حال روشن کردن ۴ اکانت...")
    await asyncio.gather(
        acc1.start(),
        acc2.start(),
        acc3.start(),
        acc4.start()
    )
    print("هر ۴ اکانت با موفقیت در گروه Linkkadde1 فعال شدند!")
    # نگه داشتن ربات‌ها روشن
    await asyncio.gather(
        *[client.idle() for client in clients]
    )

if __name__ == "__main__":
    asyncio.run(main())
