import asyncio
import sys

# --- اصلاحیه حیاتی برای پایتون ۳.۱۰ به بالا و Render ---
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# تنظیمات ربات شما
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

bot = Client("main_manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scheduler = AsyncIOScheduler()
scheduler.start()

user_states = {}
active_voice_sessions = {}

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ افزودن اکانت جدید", callback_data="add_account")],
        [InlineKeyboardButton("📋 لیست اکانت‌ها", callback_data="list_accounts"),
         InlineKeyboardButton("🗑️ حذف اکانت", callback_data="delete_account")],
        [InlineKeyboardButton("🎧 ورود اکانت به ویس‌کال", callback_data="join_voice_menu")],
        [InlineKeyboardButton("🚪 خروج از ویسکال", callback_data="leave_voice_menu")]
    ])

@bot.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    await message.reply_text(
        "🤖 **پنل حرفه‌ای مدیریت اکانت‌ها و ویس‌کال تلگرام**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu()
    )

@bot.on_callback_query(filters.regex("add_account"))
async def add_account_callback(client, callback: CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = {"step": "waiting_phone"}
    await callback.message.edit_text(
        "📱 لطفاً **شماره تلفن** اکانت را با کد کشور ارسال کنید (مثلاً: `989123456789+`):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]])
    )

@bot.on_message(filters.text & ~filters.command(["start"]))
async def handle_text_inputs(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id].get("step")

    if state == "waiting_phone":
        phone = message.text.strip()
        user_states[user_id]["phone"] = phone
        
        session_name = f"{SESSIONS_DIR}/{phone}"
        app = Client(session_name, api_id=API_ID, api_hash=API_HASH, in_memory=True)
        await app.connect()
        
        try:
            sent_code = await app.send_code(phone)
            user_states[user_id]["app"] = app
            user_states[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            user_states[user_id]["step"] = "waiting_code"
            await message.reply_text("✉️ کد تایید تلگرام ارسال شد. لطفاً **کد دریافتی** را ارسال کنید:")
        except Exception as e:
            await app.disconnect()
            user_states.pop(user_id, None)
            await message.reply_text(f"❌ خطا در ارسال کد: {e}\nمجدداً از /start شروع کنید.")

    elif state == "waiting_code":
        code = message.text.strip()
        app = user_states[user_id]["app"]
        phone = user_states[user_id]["phone"]
        phone_code_hash = user_states[user_id]["phone_code_hash"]

        try:
            await app.sign_in(phone, phone_code_hash, code)
            await app.disconnect()
            
            final_app = Client(f"{SESSIONS_DIR}/{phone}", api_id=API_ID, api_hash=API_HASH)
            await final_app.start()
            await final_app.stop()
            
            user_states.pop(user_id, None)
            await message.reply_text("✅ اکانت با موفقیت اضافه شد!", reply_markup=main_menu())
        except Exception as e:
            if "SessionPasswordNeeded" in str(e):
                user_states[user_id]["step"] = "waiting_password"
                await message.reply_text("🔐 این اکانت دارای **رمز عبور دو مرحله‌ای (2FA)** است. لطفاً رمز خود را وارد کنید:")
            else:
                user_states.pop(user_id, None)
                await message.reply_text(f"❌ خطا در ورود: {e}\nمجدداً از /start شروع کنید.")

    elif state == "waiting_password":
        password = message.text.strip()
        app = user_states[user_id]["app"]
        phone = user_states[user_id]["phone"]
        
        try:
            await app.check_password(password)
            await app.disconnect()

            final_app = Client(f"{SESSIONS_DIR}/{phone}", api_id=API_ID, api_hash=API_HASH)
            await final_app.start()
            await final_app.stop()

            user_states.pop(user_id, None)
            await message.reply_text("✅ اکانت با رمز دو مرحله‌ای با موفقیت اضافه شد!", reply_markup=main_menu())
        except Exception as e:
            user_states.pop(user_id, None)
            await message.reply_text(f"❌ رمز عبور اشتباه است یا خطایی رخ داد: {e}\nمجدداً از /start شروع کنید.")

    elif user_states[user_id].get("step") == "waiting_voice_link":
        link = message.text.strip()
        phone = user_states[user_id]["selected_account"]
        user_states.pop(user_id, None)

        status_msg = await message.reply_text(f"⏳ در حال اتصال اکانت `+{phone}` به ویس‌کال گروه...")
        
        try:
            acc_client = Client(f"{SESSIONS_DIR}/{phone}", api_id=API_ID, api_hash=API_HASH)
            await acc_client.start()
            
            chat = await acc_client.join_chat(link)
            chat_id = chat.id

            call_client = PyTgCalls(acc_client)
            await call_client.start()
            
            # برای ماندن در ویس نیاز به یک فایل صوتی کوچک مثل silent.wav یا استریم دارید
            await call_client.join_group_call(
                chat_id,
                AudioPiped("silent.wav")
            )

            async def auto_leave():
                try:
                    await call_client.leave_group_call(chat_id)
                    await acc_client.stop()
                    active_voice_sessions.pop(phone, None)
                except:
                    pass

            # ثبت تایمر ۲ ساعته خروج خودکار
            job = scheduler.add_job(auto_leave, 'interval', hours=2)
            
            active_voice_sessions[phone] = {
                "acc_client": acc_client,
                "call_client": call_client,
                "chat_id": chat_id,
                "job": job
            }

            await status_msg.edit_text(
                f"✅ اکانت `+{phone}` با موفقیت وارد ویس‌کال شد!\n"
                f"⏱️ تایمر **۲ ساعته** برای خروج خودکار فعال شد.",
                reply_markup=main_menu()
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ خطا در اتصال به ویس‌کال: {e}", reply_markup=main_menu())

@bot.on_callback_query(filters.regex("list_accounts"))
async def list_accounts_callback(client, callback: CallbackQuery):
    sessions = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    
    if not sessions:
        text = "📭 هیچ اکانتی تاکنون اضافه نشده است."
    else:
        text = "📋 **لیست اکانت‌های ثبت‌شده:**\n\n"
        for idx, acc in enumerate(sessions, 1):
            status = "🟢 (در ویس)" if acc in active_voice_sessions else "⚪️ (آفلاین/آزاد)"
            text += f"{idx}. `+{acc}` ── {status}\n"

    await callback.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]])
    )

@bot.on_callback_query(filters.regex("delete_account"))
async def delete_account_menu(client, callback: CallbackQuery):
    sessions = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    if not sessions:
        await callback.message.edit_text(
            "📭 اکانتی برای حذف وجود ندارد.", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]])
        )
        return

    keyboard = [[InlineKeyboardButton(f"🗑️ حذف `+{acc}`", callback_data=f"del_{acc}")] for acc in sessions]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")])
    
    await callback.message.edit_text("🗑️ اکانت مورد نظر جهت حذف را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query(filters.regex(r"^del_"))
async def perform_delete(client, callback: CallbackQuery):
    phone = callback.data.replace("del_", "")
    
    if phone in active_voice_sessions:
        try:
            await active_voice_sessions[phone]["call_client"].leave_group_call(active_voice_sessions[phone]["chat_id"])
            await active_voice_sessions[phone]["acc_client"].stop()
            active_voice_sessions[phone]["job"].remove()
            active_voice_sessions.pop(phone, None)
        except:
            pass

    session_file = f"{SESSIONS_DIR}/{phone}.session"
    if os.path.exists(session_file):
        os.remove(session_file)
        await callback.message.edit_text(f"✅ اکانت `+{phone}` با موفقیت حذف شد.", reply_markup=main_menu())
    else:
        await callback.message.edit_text("❌ فایل اکانت پیدا نشد.", reply_markup=main_menu())

@bot.on_callback_query(filters.regex("join_voice_menu"))
async def join_voice_menu(client, callback: CallbackQuery):
    sessions = [f.replace(".session", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]
    if not sessions:
        await callback.message.edit_text(
            "📭 اول باید حداقل یک اکانت اضافه کنید.", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]])
        )
        return

    keyboard = [[InlineKeyboardButton(f"🎧 استفاده از `+{acc}`", callback_data=f"useacc_{acc}")] for acc in sessions]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")])
    
    await callback.message.edit_text("🎧 اکانتی که می‌خواهید با آن وارد ویس شوید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query(filters.regex(r"^useacc_"))
async def select_account_for_voice(client, callback: CallbackQuery):
    phone = callback.data.replace("useacc_", "")
    user_id = callback.from_user.id
    user_states[user_id] = {"step": "waiting_voice_link", "selected_account": phone}
    
    await callback.message.edit_text(
        f"🔗 اکانت انتخابی: `+{phone}`\n\n"
        "اکنون **لینک گروه یا کانال** مورد نظر را ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]])
    )

@bot.on_callback_query(filters.regex("leave_voice_menu"))
async def leave_voice_menu(client, callback: CallbackQuery):
    if not active_voice_sessions:
        await callback.message.edit_text(
            "📭 هیچ اکانتی در حال حاضر در ویس فعال نیست.", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")]])
        )
        return

    keyboard = [[InlineKeyboardButton(f"🚪 خروج `+{phone}` از ویس", callback_data=f"leave_{phone}")] for phone in active_voice_sessions]
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_home")])
    
    await callback.message.edit_text("🚪 اکانتی که می‌خواهید از ویس خارج کنید را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

@bot.on_callback_query(filters.regex(r"^leave_"))
async def perform_leave(client, callback: CallbackQuery):
    phone = callback.data.replace("leave_", "")
    if phone in active_voice_sessions:
        try:
            session_data = active_voice_sessions[phone]
            await session_data["call_client"].leave_group_call(session_data["chat_id"])
            await session_data["acc_client"].stop()
            session_data["job"].remove()
            active_voice_sessions.pop(phone, None)
            
            await callback.message.edit_text(f"✅ اکانت `+{phone}` با موفقیت از ویس خارج شد.", reply_markup=main_menu())
        except Exception as e:
            await callback.message.edit_text(f"❌ خطا در خروج: {e}", reply_markup=main_menu())
    else:
        await callback.message.edit_text("❌ این اکانت در لیست ویس‌های فعال نیست.", reply_markup=main_menu())

@bot.on_callback_query(filters.regex("back_home"))
async def back_home(client, callback: CallbackQuery):
    user_states.pop(callback.from_user.id, None)
    await callback.message.edit_text(
        "🤖 **پنل حرفه‌ای مدیریت اکانت‌ها و ویس‌کال تلگرام**\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=main_menu()
    )

if __name__ == "__main__":
    print("Bot is running...")
    bot.run()
