import os
from pyrogram import Client, filters
from pyrogram.types import Message
from google import genai

# --- اطلاعات تلگرام شما ---
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

# کلید هوش مصنوعی را اینجا جایگزین کنید
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

# یوزرنیم گروه شما
TARGET_GROUP = "Linkkadde1"

# راه‌اندازی کلاینت‌ها
ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = Client("management_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_account_client = None

# دستورالعمل هوش مصنوعی برای پاسخگویی در گروه
SYSTEM_INSTRUCTION = """
تو یک دستیار هوشمند و صمیمی در یک گروه تلگرامی هستی.
پاسخ‌ها را کوتاه، دوستانه، جذاب و به زبان فارسی ارسال کن.
تلاش کن گفتگوهای داخل گروه را گرم و فعال نگه‌داری.
"""

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "سلام! به ربات مدیریت هوشمند گروه خوش آمدید.\n\n"
        "برای اتصال اکانت شخصی، لطفاً **String Session** خود را ارسال کنید:\n"
        "`/connect STRING_SESSION`"
    )

@bot.on_message(filters.command("connect") & filters.private)
async def connect_userbot(client: Client, message: Message):
    global user_account_client
    
    if len(message.command) < 2:
        await message.reply_text("❌ لطفاً String Session را ارسال کنید.\nمثال:\n`/connect YOUR_STRING_SESSION`")
        return

    session_string = message.text.split(maxsplit=1)[1].strip()
    await message.reply_text("⏳ در حال متصل شدن به اکانت...")

    try:
        user_account_client = Client(
            "user_session",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string
        )

        # فیلتر برای پاسخگویی فقط در گروه Linkkadde1
        @user_account_client.on_message(filters.chat(TARGET_GROUP) & ~filters.me & ~filters.bot)
        async def handle_group_message(user_cli: Client, user_msg: Message):
            if not user_msg.text:
                return

            try:
                response = ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_msg.text,
                    config={"system_instruction": SYSTEM_INSTRUCTION},
                )
                
                ai_reply = response.text.strip()
                await user_msg.reply_text(ai_reply)

            except Exception as e:
                print(f"خطا در پاسخگویی: {e}")

        await user_account_client.start()
        me = await user_account_client.get_me()
        await message.reply_text(f"✅ اکانت `{me.first_name}` متصل شد و فقط به پیام‌های گروه **Linkkadde1** پاسخ خواهد داد!")

    except Exception as e:
        await message.reply_text(f"❌ خطا در اتصال:\n`{e}`")

if __name__ == "__main__":
    print("ربات در حال اجرا است...")
    bot.run()
