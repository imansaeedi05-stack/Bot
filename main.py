import os
import asyncio
from aiohttp import web
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

ai_client = genai.Client(api_key=GEMINI_API_KEY)
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
        user_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        await user_client.connect()

        if not await user_client.is_user_authorized():
            await event.respond("❌ سشن نامعتبر است یا منقضی شده است.")
            return

        me = await user_client.get_me()

        @user_client.on(events.NewMessage(chats=TARGET_GROUP))
        async def handle_group_message(msg_event):
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
                await msg_event.reply(response.text.strip())
            except Exception as e:
                print(f"خطا: {e}")

        await event.respond(f"✅ اکانت `{me.first_name}` متصل شد!")
    except Exception as e:
        await event.respond(f"❌ خطا: `{e}`")

# سرور وب کوچک برای پاسخ به پورت رندر
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

if __name__ == "__main__":
    print("ربات در حال اجرا است...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    bot.run_until_disconnected()
