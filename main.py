import os
import logging
import asyncio
from flask import Flask
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ایمپورت ایمن برای جلوگیری از کرش کردن ربات
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types.input_stream import InputStream
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
        "ربات به صورت کامل متصل است. از دستور `/joinvc لینک_گروه` برای ورود به ویس استفاده کنید.",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex(r"^menu_"))
async def callback_menu(client, callback_query):
    data = callback_query.data
    if data == "menu_add":
        await callback_query.message.edit_text("📱 بخش افزودن اکانت آماده است.")
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
        await callback_query.answer("❌ اکانتی برای حذف وجود ندارد.", show_alert=True)
    elif data == "menu_reload":
        await load_saved_sessions()
        await callback_query.answer(f"✅ بازخوانی شد. اکانت‌ها: {len(user_clients)}", show_alert=True)

@bot.on_message(filters.command("joinvc"))
async def join_vc(client, message):
    if not PYTGCALLS_AVAILABLE:
        await message.reply_text("❌ پکیج `py-tgcalls` روی سرور نصب نیست یا نسخه آن هماهنگ نیست.")
        return

    if len(message.command) < 2:
        await message.reply_text("❌ لطفاً لینک یا آیدی گروه را وارد کنید.\nمثال: `/joinvc @username`")
        return

    target = message.command[1]
    await load_saved_sessions()

    if not pytgcalls_clients:
        await message.reply_text("❌ هیچ کلاینت فعالی برای اتصال به ویس‌‌چت وجود ندارد.")
        return

    msg = await message.reply_text("⏳ در حال اتصال اکانت‌ها به ویس‌‌چت...")
    success = 0
    
    for phone, call_client in pytgcalls_clients.items():
        user_cli = user_clients[phone]
        try:
            chat = await user_cli.get_chat(target)
            await call_client.join_group_call(chat.id)
            success += 1
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error joining VC with {phone}: {e}")

    await msg.edit_text(f"✅ عملیات اتصال به پایان رسید.\nموفق: {success} اکانت")

@bot.on_message(filters.command("leavevc"))
async def leave_vc(client, message):
    if not PYTGCALLS_AVAILABLE:
        return
    
    msg = await message.reply_text("⏳ در حال خروج از ویس‌‌چت...")
    for phone, call_client in pytgcalls_clients.items():
        try:
            await call_client.leave_group_call()
        except Exception as e:
            logger.error(f"Error leaving VC with {phone}: {e}")
    await msg.edit_text("✅ تمامی اکانت‌ها از ویس‌‌چت خارج شدند.")

if __name__ == "__main__":
    bot.run()
