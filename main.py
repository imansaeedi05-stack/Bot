import os
import asyncio
from telethon import TelegramClient, events
from google import genai

# --- اطلاعات تلگرام شما ---
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

# کلید هوش مصنوعی 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# یوزرنیم گروه شما
TARGET_GROUP = "Linkkadde1"

# راه‌اندازی کلاینت هوش مصنوعی
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# راه‌اندازی ربات اصلی مدیریت با Telethon
bot = TelegramClient('management_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_client = None

SYSTEM_INSTRUCTION = """
تو یک دستیار هوشمند و صمیمی در یک گروه تلگرامی هستی.
پاسخ‌ها را کوتاه، دوستانه، جذاب و به زبان فارسی ارسال کن.
تلاش کن گفتگوهای داخل گروه را گرم و فعال نگه‌داری.
"""

@bot.on(events.NewMessage(pattern='/start', incoming=True))
async def start_handler(event):
    if event.is_private:
        await event.respond(
            "سلام! به ربات مدیریت هوشمند گروه خوش آمدید.\n\n"
            "برای اتصال اکانت شخصی، لطفاً **Telethon String Session** خود را ارسال کنید:\n"
            "`/connect STRING_SESSION`"
        )

@bot.on(events.NewMessage(pattern='/connect', incoming=True))
async def connect_userbot(event):
    global user_client
    if not event.is_private:
        return
        
    parts = event.text.split(maxsplit=1)
    if len(parts) < 2:
        await event.respond("❌ لطفاً String Session را ارسال کنید.\nمثال:\n`/connect YOUR_STRING_SESSION`")
        return

    session_string = parts[1].strip()
    await event.respond("⏳ در حال متصل شدن به اکانت...")

    try:
        from telethon.sessions import StringSession
        
        # ساخت کلاینت اکانت کاربر با Telethon
        user_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await user_client.connect()

        if not await user_client.is_user_authorized():
            await event.respond("❌ سشن نامعتبر است یا منقضی شده است.")
            return

        me = await user_client.get_me()

        # رویداد دریافت پیام جدید در گروه مورد نظر
        @user_client.on(events.NewMessage(chats=TARGET_GROUP))
        async def handle_group_message(msg_event):
            # اگر پیام از طرف خودمان یا ربات‌ها بود نادیده بگیر
            if msg_event.out or msg_event.sender.bot:
                return
            
            msg_text = msg_event.raw_text
            if not msg_text:
                return

            try:
                response = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=msg_text,
                    config={"system_instruction": SYSTEM_INSTRUCTION},
                )
                
                ai_reply = response.text.strip()
                # ریپلای کردن به پیام ممبر در گروه
                await msg_event.reply(ai_reply)

            except Exception as e:
                print(f"خطا در پاسخگویی هوش مصنوعی: {e}")

        await event.respond(f"✅ اکانت `{me.first_name}` با موفقیت متصل شد و فقط به پیام‌های گروه **Linkkadde1** پاسخ خواهد داد!")

    except Exception as e:
        await event.respond(f"❌ خطا در اتصال:\n`{e}`")

if __name__ == "__main__":
    print("ربات مدیریت با Telethon در حال اجرا است...")
    bot.run_until_disconnected()
