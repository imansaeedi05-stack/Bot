import os
import logging
import asyncio
from flask import Flask
import threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

try:
    from pytgcalls import GroupCallFactory
    HAS_GROUP_CALL_FACTORY = True
except ImportError:
    HAS_GROUP_CALL_FACTORY = False
    try:
        from pytgcalls import PyTgCalls
    except ImportError:
        pass

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

def create_call_client(client):
    if HAS_GROUP_CALL_FACTORY:
        return GroupCallFactory(client).get_group_call()
    else:
        return PyTgCalls(client)

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
            
            call_app = create_call_client(client)
            await call_app.start()

            user_clients[phone] = client
            pytgcalls_clients[phone] = call_app
        except Exception as e:
            logger.error(f"Error loading {phone}: {e}")

async def resolve_and_join_chat(user_client: Client, target: str) -> int:
    target = target.strip()
    if "+" in target or "joinchat" in target:
        try:
            chat = await user_client.join_chat(target)
            return chat.id
        except Exception:
            chat = await user_client.get_chat(target)
            return chat.id

    if "t.me/" in target:
        target = "@" + target.split("t.me/")[-1].replace("/", "")
    elif not target.startswith("@") and not target.startswith("-100") and not target.lstrip("-").isdigit():
        target = "@" + target

    if isinstance(target, str) and (target.startswith("-100") or target.lstrip("-").isdigit()):
        target = int(target)

    try:
        chat = await user_client.get_chat(target)
        return chat.id
    except Exception:
        chat = await user_client.join_chat(target)
        return chat.id

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
        "🤖 **پنل مدیریت پیشرفته اکانت‌های ویس‌چت**\n\n"
        "از دکمه‌های شیشه‌ای زیر برای مدیریت سریع ربات استفاده کنید:",
        reply_markup=keyboard
    )

@bot.on_callback_query(filters.regex(r"^menu_"))
async def callback_menu(client, callback_query):
    data = callback_query.data
    if data == "menu_add":
        await callback_query.message.edit_text("📱 برای افزودن اکانت از اسکریپت لایسنس یا لاگین استفاده کنید.")
    elif data == "menu_list":
        await load_saved_sessions()
        if not user_clients:
            await callback_query.answer("❌ هیچ اکانتی فعال نیست.", show_alert=True)
            return
        text = f"📋 **تعداد کل اکانت‌های آماده:** {len(user_clients)}\n\n"
        for phone in user_clients.keys():
            text += f"👤 `{phone}`\n"
        await callback_query.message.edit_text(text)
    elif data == "menu_del":
        await callback_query.answer("❌ هیچ اکانتی برای حذف وجود ندارد.", show_alert=True)
    elif data == "menu_reload":
        await load_saved_sessions()
        await callback_query.answer(f"✅ بازخوانی شد. اکانت‌ها: {len(user_clients)}", show_alert=True)

@bot.on_message(filters.command("joinvc"))
async def join_vc(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ لطفاً لینک یا یوزرنیم گروه را وارد کنید.\nمثال: `/joinvc @username`")
        return

    target = message.command[1]
    await load_saved_sessions()

    if not pytgcalls_clients:
        await message.reply_text("❌ هیچ اکانت فعالی برای ورود به ویس‌چت یافت نشد.")
        return

    msg = await message.reply_text("⏳ در حال ورود اکانت‌ها به ویس‌چت...")
    joined = 0
    failed = 0

    for phone, call_app in list(pytgcalls_clients.items()):
        user_cli = user_clients[phone]
        try:
            chat_id = await resolve_and_join_chat(user_cli, target)
            await call_app.join_group_call(chat_id)
            joined += 1
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error joining {phone}: {e}")
            failed += 1

    await msg.edit_text(f"✅ عملیات ورود به ویس‌چت انجام شد!\n\n🔹 موفق: {joined}\n⚠️ ناموفق: {failed}")

@bot.on_message(filters.command("leavevc"))
async def leave_vc(client, message):
    msg = await message.reply_text("⏳ در حال خروج اکانت‌ها از ویس‌چت...")
    for phone, call_app in list(pytgcalls_clients.items()):
        try:
            if hasattr(call_app, "active_calls"):
                for call in call_app.active_calls:
                    await call_app.leave_group_call(call.chat_id)
        except Exception as e:
            logger.error(f"Error leaving {phone}: {e}")
    await msg.edit_text("✅ خروج تمامی اکانت‌ها از ویس‌چت انجام شد.")

if __name__ == "__main__":
    bot.run()
