import asyncio
import logging
import os
import re
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls.pytgcalls import PyTgCalls

app = Flask("")


@app.route("/")
def home():
  return "Bot is Alive!"


def run_flask():
  app.run(host="0.0.0.0", port=8080)


threading.Thread(target=run_flask, daemon=True).start()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8610788849:AAFu-oLDMAyFNUYN8RRi6oRM7XeHJ58q-Fs"
OWNER_ID = 7165683193

bot = Client("bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_clients = {}
pytgcalls_clients = {}
user_login_steps = {}


def is_owner(_, __, message: Message):
  return bool(message.from_user and message.from_user.id == OWNER_ID)


owner_filter = filters.create(is_owner)

SESSIONS_DIR = "sessions"
if not os.path.exists(SESSIONS_DIR):
  os.makedirs(SESSIONS_DIR)


async def keep_alive_task():
  while True:
    await asyncio.sleep(45)
    for phone, user_cli in list(user_clients.items()):
      try:
        if user_cli.is_connected:
          await user_cli.get_me()
        else:
          await user_cli.connect()
      except Exception as e:
        logger.warning(f"Error pinging {phone}: {e}")


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
      
      call_app = PyTgCalls(client)
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
  elif (
      not target.startswith("@")
      and not target.startswith("-100")
      and not target.lstrip("-").isdigit()
  ):
    target = "@" + target

  if isinstance(target, str) and (
      target.startswith("-100") or target.lstrip("-").isdigit()
  ):
    target = int(target)

  try:
    chat = await user_client.get_chat(target)
    return chat.id
  except Exception:
    chat = await user_client.join_chat(target)
    return chat.id


@bot.on_message(filters.command("start") & owner_filter)
async def start_cmd(client, message):
  text = (
      "🤖 **ربات مدیریت اکانت‌های ویس‌چت**\n\n"
      "🔹 `/addacc` - افزودن اکانت جدید\n"
      "🔹 `/accounts` - لیست اکانت‌های فعال\n"
      "🔹 `/delacc` - حذف و مدیریت اکانت‌ها\n"
      "🔹 `/joinvc <لینک/یوزرنیم>` - ورود تمام اکانت‌ها به ویس‌کال\n"
      "🔹 `/leavevc` - خروج اکانت‌ها از ویس‌کال\n"
      "🔹 `/reload` - بازیابی مجدد سشن‌ها\n"
  )
  await message.reply_text(text)


@bot.on_message(filters.command("addacc") & owner_filter)
async def add_acc(client, message):
  user_login_steps[message.from_user.id] = {"step": "phone"}
  await message.reply_text(
      "📱 شماره تلفن را با کد کشور بفرستید (مثال: `+989123456789`):"
  )


@bot.on_message(filters.command("accounts") & owner_filter)
async def list_accs(client, message):
  await load_saved_sessions()
  if not user_clients:
    await message.reply_text("❌ هیچ اکانتی فعال نیست.")
    return
  text = f"📋 **تعداد کل اکانت‌های آماده:** {len(user_clients)}\n\n"
  for phone in user_clients.keys():
    text += f"👤 `{phone}`\n"
  await message.reply_text(text)


@bot.on_message(filters.command("delacc") & owner_filter)
async def del_acc_cmd(client, message):
  await load_saved_sessions()
  if not user_clients:
    await message.reply_text("❌ هیچ اکانتی برای حذف وجود ندارد.")
    return

  buttons = []
  for phone in user_clients.keys():
    buttons.append([
        InlineKeyboardButton(f"🗑 حذف {phone}", callback_data=f"del_{phone}")
    ])

  await message.reply_text(
      "📋 **مدیریت اکانت‌ها:**\nروی اکانتی که می‌‌خواهید از ربات حذف شود کلیک"
      " کنید:",
      reply_markup=InlineKeyboardMarkup(buttons),
  )


@bot.on_callback_query(filters.regex(r"^del_"))
async def callback_del_acc(client, callback_query):
  phone = callback_query.data.replace("del_", "")

  try:
    if phone in pytgcalls_clients:
      try:
        await pytgcalls_clients[phone].stop()
      except:
        pass
      del pytgcalls_clients[phone]

    if phone in user_clients:
      try:
        await user_clients[phone].stop()
      except:
        pass
      del user_clients[phone]

    session_file = os.path.join(SESSIONS_DIR, f"{phone}.session")
    if os.path.exists(session_file):
      os.remove(session_file)

    journal_file = os.path.join(SESSIONS_DIR, f"{phone}.session-journal")
    if os.path.exists(journal_file):
      os.remove(journal_file)

    await callback_query.message.edit_text(
        f"✅ اکانت `{phone}` با موفقیت حذف شد و فایل سشن آن پاک گردید."
    )
  except Exception as e:
    await callback_query.answer(f"❌ خطا در حذف اکانت: {e}", show_alert=True)


@bot.on_message(filters.command("reload") & owner_filter)
async def reload_accs(client, message):
  msg = await message.reply_text("⏳ در حال بازیابی سشن‌ها...")
  await load_saved_sessions()
  await msg.edit_text(
      f"✅ بازخوانی تکمیل شد. اکانت‌های آماده: {len(user_clients)}"
  )


@bot.on_message(filters.text & filters.private & owner_filter)
async def handle_login(client, message):
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
      await message.reply_text("📩 کد ۵ رقمی را بفرستید:")
    except Exception as e:
      await message.reply_text(f"❌ خطا: {e}")
      del user_login_steps[user_id]

  elif step == "code":
    code = message.text.strip()
    temp_client = step_data["client"]
    phone = step_data["phone"]
    try:
      await temp_client.sign_in(phone, step_data["hash"], code)
      call_app = PyTgCalls(temp_client)
      await call_app.start()

      user_clients[phone] = temp_client
      pytgcalls_clients[phone] = call_app
      del user_login_steps[user_id]
      await message.reply_text(f"✅ اکانت ذخیره شد: `{phone}`")
    except SessionPasswordNeeded:
      step_data["step"] = "password"
      await message.reply_text("🔑 رمز دو مرحله‌ای را بفرستید:")
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
      call_app = PyTgCalls(temp_client)
      await call_app.start()

      user_clients[phone] = temp_client
      pytgcalls_clients[phone] = call_app
      del user_login_steps[user_id]
      await message.reply_text(f"✅ اکانت ذخیره شد: `{phone}`")
    except PasswordHashInvalid:
      await message.reply_text("❌ رمز اشتباه است. دوباره بفرستید:")
    except Exception as e:
      await message.reply_text(f"❌ خطا: {e}")
      del user_login_steps[user_id]


@bot.on_message(filters.command("joinvc") & owner_filter)
async def join_vc(client, message):
  if len(message.command) < 2:
    await message.reply_text("❌ لطفاً لینک یا یوزرنیم گروه را وارد کنید.")
    return

  target = message.command[1]
  await load_saved_sessions()

  if not pytgcalls_clients:
    await message.reply_text("❌ هیچ اکانتی یافت نشد.")
    return

  msg = await message.reply_text("⏳ در حال ورود دسته‌ای اکانت‌ها به ویس‌چت...")
  joined = 0
  failed = 0

  for phone, call_app in list(pytgcalls_clients.items()):
    user_cli = user_clients[phone]
    try:
      chat_id = await resolve_and_join_chat(user_cli, target)
      await call_app.join_group_call(chat_id)
      joined += 1

      if joined % 5 == 0:
        await msg.edit_text(
            f"⏳ در حال ورود... تا الان {joined} اکانت وارد شدند."
        )

      await asyncio.sleep(2)
    except Exception as e:
      logger.error(f"Error joining {phone}: {e}")
      failed += 1

  await msg.edit_text(
      f"✅ ورود دسته‌ای کامل شد!\n\n🔹 موفق: {joined}\n⚠️ ناموفق: {failed}"
  )


@bot.on_message(filters.command("leavevc") & owner_filter)
async def leave_vc(client, message):
  msg = await message.reply_text("⏳ در حال خروج اکانت‌ها از ویس‌چت...")
  left = 0
  for phone, call_app in list(pytgcalls_clients.items()):
    try:
      for call in call_app.active_calls:
        await call_app.leave_group_call(call.chat_id)
        left += 1
    except Exception as e:
      logger.error(f"Error leaving {phone}: {e}")

  await msg.edit_text("✅ خروج اکانت‌ها انجام شد.")


async def main():
  await bot.start()
  await bot.delete_webhook()
  await load_saved_sessions()
  asyncio.create_task(keep_alive_task())
  await asyncio.Event().wait()


if __name__ == "__main__":
  asyncio.run(main())
