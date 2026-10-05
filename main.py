import os
import asyncio

# اصلاح حیاتی پیش از هرگونه ایمپورت Pyrogram برای پایتون در رندر
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import re
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped

BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"

bot = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

SESSIONS_DIR = "sessions"
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

pytgcalls_clients = {}
user_steps = {}
SILENT_AUDIO = "silent.wav"

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "🤖 **سیستم مدیریت اکانت‌ها و ویس‌کال (نسخه py-tgcalls v2)**\n\n"
        "دستورات موجود:\n"
        "➕ `/add` - افزودن اکانت جدید (شماره، کد، رمز)\n"
        "📋 `/list` - لیست اکانت‌های فعال\n"
        "🎧 `/join آیدی_گروه` - ورود تمام اکانت‌ها به ویس‌کال\n"
        "🚪 `/leave` - خروج تمام اکانت‌ها از ویس‌کال"
    )

@bot.on_message(filters.command("add") & filters.private)
async def add_account_cmd(client, message):
    user_id = message.from_user.id
    user_steps[user_id] = {"step": "phone"}
    await message.reply_text("📱 لطفاً شماره تلفن اکانت خود را با کد کشور بفرستید:\n(مثال: `+989123456789`)")

@bot.on_message(filters.command("list") & filters.private)
async def list_accounts_cmd(client, message):
    session_files = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    if not session_files:
        await message.reply_text("❌ هیچ اکانتی ذخیره نشده است.")
        return
    text = f"📋 **تعداد اکانت‌ها:** {len(session_files)}\n\n"
    for phone in session_files:
        text += f"👤 `+{phone}`\n"
    await message.reply_text(text)

@bot.on_message(filters.command("join") & filters.private)
async def join_vc_cmd(client, message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ لطفاً لینک یا آیدی گروه را وارد کنید.\nمثال: `/join Linkkadde1`")
        return
    
    target = args[1].strip()
    if "t.me/" in target:
        target = target.split("t.me/")[-1].split("/")[0]
    target = target.strip("@")

    session_files = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    if not session_files:
        await message.reply_text("❌ هیچ اکانتی برای ورود به ویس وجود ندارد اول با دستور `/add` اکانت اضافه کنید.")
        return

    status_msg = await message.reply_text(f"⏳ در حال اتصال {len(session_files)} اکانت به ویس‌چت...")
    success = 0
    errors = []

    for phone in session_files:
        session_path = os.path.join(SESSIONS_DIR, phone)
        try:
            user_cli = Client(session_path, api_id=API_ID, api_hash=API_HASH)
            await user_cli.start()

            chat = await user_cli.join_chat(target)
            chat_id = chat.id

            # ساخت و راه‌اندازی کلاینت ویس برای py-tgcalls v2
            call_client = PyTgCalls(user_cli)
            await call_client.start()
            pytgcalls_clients[phone] = call_client

            if os.path.exists(SILENT_AUDIO):
                await call_client.join(chat_id, AudioPiped(SILENT_AUDIO))
            else:
                await call_client.join(chat_id)

            success += 1
            await asyncio.sleep(3)
        except Exception as e:
            errors.append(f"اکانت `+{phone}`: {e}")

    report = f"✅ موفق: {success} اکانت متصل شدند."
    if errors:
        report += f"\n\n❌ **خطاها:**\n" + "\n".join(errors)
    await status_msg.edit_text(report)

@bot.on_message(filters.command("leave") & filters.private)
async def leave_vc_cmd(client, message):
    status_msg = await message.reply_text("⏳ در حال خروج اکانت‌ها از ویس‌کال...")
    left_count = 0
    for phone, call_client in pytgcalls_clients.items():
        try:
            await call_client.leave()
            left_count += 1
        except Exception:
            pass
    pytgcalls_clients.clear()
    await status_msg.edit_text(f"✅ {left_count} اکانت با موفقیت از ویس خارج شدند.")

@bot.on_message(filters.text & filters.private)
async def handle_steps(client, message):
    user_id = message.from_user.id
    if user_id not in user_steps:
        return

    data = user_steps[user_id]
    step = data.get("step")

    if step == "phone":
        phone = re.sub(r"\s+", "", message.text.strip())
        session_path = os.path.join(SESSIONS_DIR, phone.replace("+", ""))
        temp_client = Client(session_path, api_id=API_ID, api_hash=API_HASH)
        await temp_client.connect()
        try:
            sent_code = await temp_client.send_code(phone)
            data.update({"step": "code", "phone": phone, "client": temp_client, "hash": sent_code.phone_code_hash})
            await message.reply_text("📩 کد تلگرام ارسال شد. لطفاً کد را بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا در ارسال کد: {e}")
            del user_steps[user_id]

    elif step == "code":
        code = message.text.strip()
        temp_client = data["client"]
        phone = data["phone"]
        try:
            await temp_client.sign_in(phone, data["hash"], code)
            await temp_client.disconnect()
            del user_steps[user_id]
            await message.reply_text(f"✅ اکانت `+{phone}` با موفقیت اضافه و ذخیره شد!")
        except SessionPasswordNeeded:
            data["step"] = "password"
            await message.reply_text("🔑 این اکانت رمز دو مرحله‌ای (Password) دارد. لطفاً رمز خود را وارد کنید:")
        except PhoneCodeInvalid:
            await message.reply_text("❌ کد وارد شده اشتباه است. دوباره کد را بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا: {e}")
            del user_steps[user_id]

    elif step == "password":
        password = message.text.strip()
        temp_client = data["client"]
        phone = data["phone"]
        try:
            await temp_client.check_password(password)
            await temp_client.disconnect()
            del user_steps[user_id]
            await message.reply_text(f"✅ اکانت `+{phone}` با رمز عبور تایید و ذخیره شد!")
        except Exception as e:
            await message.reply_text(f"❌ رمز عبور اشتباه است یا خطایی رخ داد: {e}")
            del user_steps[user_id]

if __name__ == "__main__":
    bot.run()
