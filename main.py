import os
import logging
import asyncio
import re
from flask import Flask
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PasswordHashInvalid

try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import AudioPiped
    PYTGCALLS_AVAILABLE = True
except Exception:
    PYTGCALLS_AVAILABLE = False

app = Flask("")

@app.route("/")
def home():
    return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"

bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_clients = {}
pytgcalls_clients = {}
user_login_steps = {}

SESSIONS_DIR = "sessions"
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# ساخت یک فایل صوتی خالی یا پیش‌فرض برای جلوگیری از ارور نبود صدا در ویس‌چت
SILENT_AUDIO = "silent.raw"
if not os.path.exists(SILENT_AUDIO):
    try:
        with open(SILENT_AUDIO, "wb") as f:
            f.write(b"\0" * 10240)  # ساخت چند کیلوبایت داده صوتی خالی
    except Exception:
        pass

async def load_saved_sessions():
    global user_clients, pytgcalls_clients
    if not os.path.exists(SESSIONS_DIR):
        return

    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    for file in session_files:
        phone = file.replace(".session", "")
        if phone in user_clients and user_clients[phone].is_connected:
            continue
        try:
            session_path = os.path.join(SESSIONS_DIR, phone)
            client = Client(session_path, api_id=API_ID, api_hash=API_HASH)
            await client.start()
            user_clients[phone] = client
            
            if PYTGCALLS_AVAILABLE and phone not in pytgcalls_clients:
                call_client = PyTgCalls(client)
                await call_client.start()
                pytgcalls_clients[phone] = call_client
        except Exception as e:
            logger.error(f"Error loading session {phone}: {e}")

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ افزودن اکانت", callback_data="panel_add"),
            InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data="panel_list"),
        ],
        [
            InlineKeyboardButton("🎧 ورود به ویس‌چت", callback_data="panel_joinvc"),
            InlineKeyboardButton("🚪 خروج از ویس", callback_data="panel_leavevc"),
        ],
        [
            InlineKeyboardButton("🗑 حذف اکانت", callback_data="panel_del"),
            InlineKeyboardButton("🔄 بازخوانی سشن‌ها", callback_data="panel_reload"),
        ],
    ])

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "🤖 **پنل مدیریت پیشرفته اکانت‌ها و ویس‌چت**\n\n"
        "لطفاً از دکمه‌های زیر استفاده کنید:",
        reply_markup=get_main_keyboard()
    )

@bot.on_callback_query(filters.regex(r"^panel_"))
async def callback_panel(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "panel_add":
        user_login_steps[user_id] = {"step": "phone"}
        await callback_query.message.edit_text(
            "📱 لطفاً شماره تلفن اکانت خود را با کد کشور بفرستید:\n(مثال: `+989123456789`)"
        )
    elif data == "panel_list":
        await load_saved_sessions()
        if not user_clients:
            await callback_query.answer("❌ هیچ اکانت فعالی یافت نشد.", show_alert=True)
            return
        text = f"📋 **تعداد کل اکانت‌ها:** {len(user_clients)}\n\n"
        for phone in user_clients.keys():
            text += f"👤 `{phone}`\n"
        await callback_query.message.edit_text(text, reply_markup=get_main_keyboard())
    elif data == "panel_joinvc":
        user_login_steps[user_id] = {"step": "vc_target"}
        await callback_query.message.edit_text(
            "🔗 لطفاً لینک یا آیدی گروه/کانال را بفرستید\n(مثال: `chat_name` یا `@username` یا لینک دعوت):\n\n*(توجه: پیش از ورود، اکانت باید به گروه دسترسی داشته باشد)*"
        )
    elif data == "panel_leavevc":
        msg = await callback_query.message.edit_text("⏳ در حال خروج تمامی اکانت‌ها از ویس‌چت...")
        for phone, call_client in pytgcalls_clients.items():
            try:
                await call_client.leave_group_call()
            except Exception as e:
                logger.error(f"Leave error: {e}")
        await callback_query.message.edit_text("✅ تمام اکانت‌ها از ویس‌چت خارج شدند.", reply_markup=get_main_keyboard())
    elif data == "panel_del":
        await load_saved_sessions()
        if not user_clients:
            await callback_query.answer("❌ هیچ اکانتی برای حذف وجود ندارد.", show_alert=True)
            return
        buttons = [[InlineKeyboardButton(f"🗑 حذف {phone}", callback_data=f"del_{phone}")] for phone in user_clients.keys()]
        buttons.append([InlineKeyboardButton("🔙 بازگشت به منو", callback_data="panel_back")])
        await callback_query.message.edit_text(
            "🗑 اکانت مورد نظر برای حذف را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "panel_reload":
        await load_saved_sessions()
        await callback_query.answer(f"✅ بازخوانی شد. اکانت‌ها: {len(user_clients)}", show_alert=True)
    elif data == "panel_back":
        await callback_query.message.edit_text(
            "🤖 **پنل مدیریت پیشرفته اکانت‌ها و ویس‌چت**",
            reply_markup=get_main_keyboard()
        )

@bot.on_callback_query(filters.regex(r"^del_"))
async def callback_del_acc(client, callback_query):
    phone = callback_query.data.replace("del_", "")
    try:
        if phone in pytgcalls_clients:
            await pytgcalls_clients[phone].stop()
            del pytgcalls_clients[phone]
        if phone in user_clients:
            await user_clients[phone].stop()
            del user_clients[phone]

        session_file = os.path.join(SESSIONS_DIR, f"{phone}.session")
        if os.path.exists(session_file):
            os.remove(session_file)

        await callback_query.message.edit_text(f"✅ اکانت `{phone}` با موفقیت حذف شد.", reply_markup=get_main_keyboard())
    except Exception as e:
        await callback_query.answer(f"❌ خطا در حذف اکانت: {e}", show_alert=True)

@bot.on_message(filters.text & filters.private)
async def handle_user_input(client, message):
    user_id = message.from_user.id
    if user_id not in user_login_steps:
        return

    step_data = user_login_steps[user_id]
    step = step_data.get("step")

    if step == "vc_target":
        target = message.text.strip()
        del user_login_steps[user_id]
        
        if not PYTGCALLS_AVAILABLE:
            await message.reply_text("❌ پکیج ویس‌چت روی سرور فعال نیست.", reply_markup=get_main_keyboard())
            return

        await load_saved_sessions()
        if not pytgcalls_clients:
            await message.reply_text("❌ هیچ اکانت فعالی برای اتصال وجود ندارد.", reply_markup=get_main_keyboard())
            return

        if "t.me/" in target:
            target = target.split("t.me/")[-1].split("/")[0]
        if target.startswith("@"):
            target = target[1:]

        msg = await message.reply_text("⏳ در حال بررسی و اتصال اکانت‌ها به ویس‌چت...")
        success = 0
        failed_details = ""

        for phone, call_client in pytgcalls_clients.items():
            user_cli = user_clients[phone]
            try:
                chat_id = None
                if "+" in target or "joinchat" in target:
                    chat = await user_cli.join_chat(target)
                    chat_id = chat.id
                else:
                    try:
                        chat = await user_cli.join_chat(target)
                        chat_id = chat.id
                    except Exception:
                        chat_obj = await user_cli.get_chat(target)
                        chat_id = chat_obj.id

                # اتصال به ویس‌چت همراه با پارامتر stream مورد نیاز در نسخه‌های جدید
                stream_source = AudioPiped(SILENT_AUDIO) if os.path.exists(SILENT_AUDIO) else None
                if stream_source:
                    await call_client.join_group_call(chat_id, stream_source)
                else:
                    await call_client.join_group_call(chat_id)

                success += 1
            except Exception as e:
                error_msg = str(e)
                logger.error(f"VC join error for {phone}: {error_msg}")
                failed_details += f"\n👤 `{phone}` ⬅️ ارور: `{error_msg}`"

        result_text = f"📊 **گزارش اتصال به ویس‌چت:**\n\n✅ اتصال موفق: {success} اکانت"
        if failed_details:
            result_text += f"\n\n⚠️ **اکانت‌های ناموفق و دلیل خطا:**{failed_details}"

        await msg.edit_text(result_text, reply_markup=get_main_keyboard())
        return

    if step == "phone":
        phone = re.sub(r"\s+", "", message.text.strip())
        session_path = os.path.join(SESSIONS_DIR, phone)
        temp_client = Client(session_path, api_id=API_ID, api_hash=API_HASH)
        await temp_client.connect()
        try:
            sent_code = await temp_client.send_code(phone)
            step_data.update({
                "step": "code",
                "phone": phone,
                "client": temp_client,
                "hash": sent_code.phone_code_hash,
            })
            await message.reply_text("📩 کد تلگرام ارسال شده را بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا در ارسال کد: {e}", reply_markup=get_main_keyboard())
            del user_login_steps[user_id]

    elif step == "code":
        code = message.text.strip()
        temp_client = step_data["client"]
        phone = step_data["phone"]
        try:
            await temp_client.sign_in(phone, step_data["hash"], code)
            
            if PYTGCALLS_AVAILABLE:
                call_client = PyTgCalls(temp_client)
                await call_client.start()
                pytgcalls_clients[phone] = call_client

            user_clients[phone] = temp_client
            del user_login_steps[user_id]
            await message.reply_text(f"✅ اکانت `{phone}` با موفقیت اضافه و ذخیره شد!", reply_markup=get_main_keyboard())
        except SessionPasswordNeeded:
            step_data["step"] = "password"
            await message.reply_text("🔑 رمز دو مرحله‌ای را وارد کنید:")
        except PhoneCodeInvalid:
            await message.reply_text("❌ کد اشتباه است. دوباره بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا: {e}", reply_markup=get_main_keyboard())
            del user_login_steps[user_id]

    elif step == "password":
        password = message.text.strip()
        temp_client = step_data["client"]
        phone = step_data["phone"]
        try:
            await temp_client.check_password(password)
            
            if PYTGCALLS_AVAILABLE:
                call_client = PyTgCalls(temp_client)
                await call_client.start()
                pytgcalls_clients[phone] = call_client

            user_clients[phone] = temp_client
            del user_login_steps[user_id]
            await message.reply_text(f"✅ رمز تایید شد و اکانت `{phone}` ذخیره شد!", reply_markup=get_main_keyboard())
        except PasswordHashInvalid:
            await message.reply_text("❌ رمز اشتباه است. دوباره بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا: {e}", reply_markup=get_main_keyboard())
            del user_login_steps[user_id]

if __name__ == "__main__":
    bot.run()
