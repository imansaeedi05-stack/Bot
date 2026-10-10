import os
import asyncio
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from google import genai

# --- اطلاعات تلگرام شما ---
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8891711180:AAHjQ-iPojdYXWOs1vT9dFRKXlzEIVyYcEU"

# کلید هوش مصنوعی 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# یوزرنیم گروه شما
TARGET_GROUP = "Linkkadde1"

ai_client = genai.Client(api_key=GEMINI_API_KEY)
bot = TelegramClient('management_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

user_client = None
user_states = {}

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
            "برای اتصال اکانت شخصی خود، دستور زیر را ارسال کنید:\n"
            "`/connect`"
        )

@bot.on(events.NewMessage(pattern='/connect', incoming=True))
async def connect_start(event):
    if not event.is_private:
        return
    user_id = event.sender_id
    
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) > 1:
        phone = parts[1].strip()
        await process_phone_number(event, user_id, phone)
    else:
        user_states[user_id] = {"step": "waiting_phone"}
        await event.respond("📞 لطفاً **شماره تلفن** اکانت تلگرام خود را با پیش‌شماره کشور بفرستید (مثلاً `905382405743+`):")

@bot.on(events.NewMessage(incoming=True))
async def interactive_auth(event):
    if not event.is_private:
        return
    user_id = event.sender_id
    if user_id not in user_states:
        return

    state = user_states[user_id]["step"]
    text = event.raw_text.strip()
    
    if text.startswith('/'):
        return

    # مرحله ۱: دریافت شماره تلفن
    if state == "waiting_phone":
        await process_phone_number(event, user_id, text)

    # مرحله ۲: دریافت کد تأیید
    elif state == "waiting_code":
        code = text
        temp_client = user_states[user_id]["temp_client"]
        phone = user_states[user_id]["phone"]
        phone_code_hash = user_states[user_id]["phone_code_hash"]

        try:
            await temp_client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            await finish_connection(event, temp_client, user_id)
        except Exception as e:
            err_str = str(e)
            # بررسی دقیق خطای رمز دوم در تلگرام
            if "SessionPasswordNeededError" in err_str or "password" in err_str.lower() or "Two-steps" in err_str:
                user_states[user_id]["step"] = "waiting_password"
                await event.respond("🔐 اکانت شما دارای رمز دوم (تایید دو مرحله‌ای) است. لطفاً **رمز عبور** خود را وارد کنید:")
            else:
                await event.respond(f"❌ خطا در ورود: `{e}`\nلطفاً دوباره با دستور `/connect` شروع کنید.")
                try:
                    await temp_client.disconnect()
                except:
                    pass
                del user_states[user_id]

    # مرحله ۳: دریافت رمز دو مرحله‌ای (Password)
    elif state == "waiting_password":
        password = text
        temp_client = user_states[user_id]["temp_client"]

        try:
            await temp_client.sign_in(password=password)
            await finish_connection(event, temp_client, user_id)
        except Exception as e:
            await event.respond(f"❌ رمز اشتباه است یا خطایی رخ داد: `{e}`\nلطفاً دوباره با دستور `/connect` امتحان کنید.")
            try:
                await temp_client.disconnect()
            except:
                pass
            del user_states[user_id]

async def process_phone_number(event, user_id, phone):
    user_states[user_id] = {"step": "waiting_code", "phone": phone}
    await event.respond(f"⏳ در حال ارسال کد تأیید به شماره `{phone}`...")
    try:
        temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await temp_client.connect()
        sent_code = await temp_client.send_code_request(phone)
        user_states[user_id]["temp_client"] = temp_client
        user_states[user_id]["phone_code_hash"] = sent_code.phone_code_hash
        await event.respond("📥 کد تأیید تلگرام برای شما ارسال شد. لطفاً **کد** را بفرستید (اعداد را پشت سر هم بدون فاصله وارد کنید):")
    except Exception as e:
        await event.respond(f"❌ خطا در ارسال کد: `{e}`\nلطفاً بررسی کنید شماره را درست وارد کرده باشید و دوباره `/connect` بفرستید.")
        if user_id in user_states:
            del user_states[user_id]

async def finish_connection(event, temp_client, user_id):
    global user_client
    user_client = temp_client
    me = await user_client.get_me()
    
    await event.respond(f"✅ اکانت `{me.first_name}` با موفقیت متصل شد و از این پس به پیام‌های گروه **{TARGET_GROUP}** پاسخ خواهد داد!")
    
    # فعال‌سازی پاسخگویی هوشمند در گروه
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
            print(f"خطا در هوش مصنوعی: {e}")

    if user_id in user_states:
        del user_states[user_id]

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

if __name__ == "__main__":
    print("ربات تعاملی ورود به اکانت در حال اجرا است...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    bot.run_until_disconnected()
