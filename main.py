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
            
            if PYTGCALLS_AVAILABLE:
                call_client = PyTgCalls(client)
                await call_client.start()
                pytgcalls_clients[phone] = call_client
        except Exception as e:
            logger.error(f"Error loading session {phone}: {e}")

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ افزودن اکانت", callback_data="menu_add"),
            InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data="menu_list"),
        ],
        [
            InlineKeyboardButton("🗑 حذف اکانت", callback_data="menu_del"),
            InlineKeyboardButton("🔄 بازخوانی سشن‌ها", callback_data="menu_reload"),
        ],
    ])

    await message.reply_text(
        "🤖 **پنل مدیریت اکانت‌ها و ویس‌چت**\n\n"
        "برای ورود به ویس‌چت از دستور زیر استفاده کنید:\n"
        "`/joinvc آیدی_یا_لینک_گروه`",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex(r"^menu_"))
async def callback_menu(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "menu_add":
        user_login_steps[user_id] = {"step": "phone"}
        await callback_query.message.edit_text(
            "📱 لطفاً شماره تلفن اکانت خود را با کد کشور بفرستید:\n(مثال: `+989123456789`)"
        )
    elif data == "menu_list":
        await load_saved_sessions()
        if not user_clients:
            await callback_query.answer("❌ هیچ اکانت فعالی یافت نشد.", show_alert=True)
            return
        text = f"📋 **تعداد اکانت‌ها:** {len(user_clients)}\n\n"
        for phone in user_clients.keys():
            text += f"👤 `{phone}`\n"
        await callback_query.message.edit_text(text)
    elif data == "menu_del":
        await load_saved_sessions()
        if not user_clients:
            await callback_query.answer("❌ هیچ اکانتی برای حذف وجود ندارد.", show_alert=True)
            return
        buttons = [[InlineKeyboardButton(f"🗑 حذف {phone}", callback_data=f"del_{phone}")] for phone in user_clients.keys()]
        await callback_query.message.edit_text(
            "🗑 اکانت مورد نظر برای حذف را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "menu_reload":
        await load_saved_sessions()
        await callback_query.answer(f"✅ بازخوانی شد. اکانت‌ها: {len(user_clients)}", show_alert=True)

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

        await callback_query.message.edit_text(f"✅ اکانت `{phone}` با موفقیت حذف شد.")
    except Exception as e:
        await callback_query.answer(f"❌ خطا در حذف اکانت: {e}", show_alert=True)

@bot.on_message(filters.text & filters.private)
async def handle_login_process(client, message):
    user_id = message.from_user.id
    if user_id not in user_login_steps:
        return

    step_data = user_login_steps[user_id]
    step = step_data.get("step")

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
            await message.reply_text(f"❌ خطا در ارسال کد: {e}")
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
            await message.reply_text(f"✅ اکانت `{phone}` با موفقیت اضافه و ذخیره شد!")
        except SessionPasswordNeeded:
            step_data["step"] = "password"
            await message.reply_text("🔑 رمز دو مرحله‌ای را وارد کنید:")
        except PhoneCodeInvalid:
            await message.reply_text("❌ کد اشتباه است. دوباره بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا: {e}")
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
            await message.reply_text(f"✅ رمز تایید شد و اکانت `{phone}` ذخیره شد!")
        except PasswordHashInvalid:
            await message.reply_text("❌ رمز اشتباه است. دوباره بفرستید:")
        except Exception as e:
            await message.reply_text(f"❌ خطا: {e}")
            del user_login_steps[user_id]

@bot.on_message(filters.command("joinvc"))
async def join_vc(client, message):
    if not PYTGCALLS_AVAILABLE:
        await message.reply_text("❌ پکیج ویس‌چت فعال نیست.")
        return

    if len(message.command) < 2:
        await message.reply_text("❌ لطفاً لینک یا آیدی گروه را وارد کنید.\nمثال: `/joinvc @username`")
        return

    target = message.command[1].strip()
    await load_saved_sessions()

    if not pytgcalls_clients:
        await message.reply_text("❌ هیچ اکانت فعالی برای اتصال وجود ندارد. اول اکانت اضافه کنید.")
        return

    msg = await message.reply_text("⏳ در حال عضویت اکانت‌ها در گروه و اتصال به ویس‌چت...")
    success = 0
    failed = 0
    
    for phone, call_client in pytgcalls_clients.items():
        user_cli = user_clients[phone]
        try:
            # ابتدا اکانت یوزر باید عضو گروه یا چت مورد نظر شود
            chat_id = target
            if "+" in target or "joinchat" in target:
                chat = await user_cli.join_chat(target)
                chat_id = chat.id
            else:
                try:
                    chat = await user_cli.join_chat(target)
                    chat_id = chat.id
                except Exception:
                    # اگر از قبل عضو بود یا با get_chat چک می‌کنیم
                    chat_obj = await user_cli.get_chat(target)
                    chat_id = chat_obj.id

            # اتصال به ویس‌چت با متد استاندارد py-tgcalls
            await call_client.join_group_call(chat_id)
            success += 1
            await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"Error joining VC with {phone}: {e}")
            failed += 1

    await msg.edit_text(f"✅ عملیات اتصال به ویس‌چت پایان یافت.\n\n🔹 موفق: {success}\n⚠️ ناموفق: {failed}")

@bot.on_message(filters.command("leavevc"))
async def leave_vc(client, message):
    if not PYTGCALLS_AVAILABLE:
        return
    
    msg = await message.reply_text("⏳ در حال خروج از ویس‌چت...")
    for phone, call_client in pytgcalls_clients.items():
        try:
            await call_client.leave_group_call()
        except Exception as e:
            logger.error(f"Error leaving VC with {phone}: {e}")
    await msg.edit_text("✅ تمامی اکانت‌ها از ویس‌چت خارج شدند.")

if __name__ == "__main__":
    bot.run()
