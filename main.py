import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired

# اطلاعات اختصاصی شما
API_ID = 38859635
API_HASH = "5232c81647167a853b97fcadf68ea9d2"
BOT_TOKEN = "8294434432:AAGpD8JW1PwaCgMaIORKG8JnSwDE8g4Xyi8"

ADMIN_ID = None  # اولین کسی که ربات را استارت بزند به عنوان ادمین شناخته می‌شود

accounts = []             
collected_users = set()   
temp_login_data = {}      

bot = Client("admin_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# تعیین ادمین خودکار با اولین استارت
@bot.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    global ADMIN_ID
    if ADMIN_ID is None:
        ADMIN_ID = message.from_user.id
        await message.reply_text(f"✅ شما به عنوان ادمین اصلی ربات ثبت شدید (`{ADMIN_ID}`).")
    
    if message.from_user.id != ADMIN_ID:
        return await message.reply_text("❌ شما اجازه دسترسی به این ربات را ندارید.")

    text = (
        "🤖 **سیستم استخراج آیدی و ارسال انبوه**\n\n"
        "1️⃣ `/login <شماره>` : شروع ورود اکانت (مثال: `/login +98912...`)\n"
        "2️⃣ `/code <کد>` : ورود کد تایید تلگرام\n"
        "3️⃣ `/password <رمز>` : ورود رمز دوم (در صورت داشتن 2FA)\n"
        "4️⃣ `/join <لینک گروه>` : **فقط اولین اکانت** وارد گروه شده و آیدی‌ها را جمع می‌کند\n"
        "5️⃣ `/send_all <متن>` : تقسیم آیدی‌ها بین تمام اکانت‌ها و ارسال امن\n"
        "6️⃣ `/stats` : مشاهده آمار اکانت‌ها و آیدی‌ها"
    )
    await message.reply_text(text)


# 1️⃣ شروع فرآیند ورود با شماره
@bot.on_message(filters.command("login"))
async def login_start(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        phone = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("❌ لطفاً شماره تلفن را جلوی دستور بنویسید.\nمثال:\n`/login +989123456789`")

    await message.reply_text(f"⏳ در حال ارسال کد تایید به شماره `{phone}`...")
    
    try:
        user_client = Client(
            name=f"acc_{phone}",
            api_id=API_ID,
            api_hash=API_HASH,
            in_memory=True
        )
        await user_client.connect()
        sent_code = await user_client.send_code(phone)
        
        temp_login_data[ADMIN_ID] = {
            "client": user_client,
            "phone": phone,
            "phone_code_hash": sent_code.phone_code_hash
        }
        
        await message.reply_text("✅ کد تایید تلگرام ارسال شد.\nحالا کد دریافتی را با دستور زیر بفرستید:\n`/code 12345`")
    except Exception as e:
        await message.reply_text(f"❌ خطا در ارسال کد: {e}")


# 2️⃣ دریافت کد تایید
@bot.on_message(filters.command("code"))
async def enter_code(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID: return
    if ADMIN_ID not in temp_login_data:
        return await message.reply_text("❌ ابتدا باید دستور `/login` را بزنید.")
    
    try:
        code = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply_text("❌ لطفاً کد را بنویسید. مثال: `/code 12345`")
        
    data = temp_login_data[ADMIN_ID]
    user_client = data["client"]
    phone = data["phone"]
    phone_code_hash = data["phone_code_hash"]
    
    try:
        await user_client.sign_in(phone, phone_code_hash, code)
        session_string = await user_client.export_session_string()
        await finalize_login(user_client, session_string, message)
        
    except SessionPasswordNeeded:
        await message.reply_text("🔒 این اکانت دارای رمز دوم (تایید دو مرحله‌ای) است.\nلطفاً رمز عبور خود را با دستور زیر بفرستید:\n`/password رمز_شما`")
        
    except (PhoneCodeInvalid, PhoneCodeExpired):
        await message.reply_text("❌ کد وارد شده اشتباه یا منقضی شده است.")
    except Exception as e:
        await message.reply_text(f"❌ خطا: {e}")


# 3️⃣ دریافت رمز دوم (در صورت نیاز)
@bot.on_message(filters.command("password"))
async def enter_password(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID: return
    if ADMIN_ID not in temp_login_data:
        return await message.reply_text("❌ فرآیند لاگین فعال نیست.")
        
    try:
        password = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply_text("❌ لطفاً رمز را بنویسید. مثال: `/password 1234`")
        
    data = temp_login_data[ADMIN_ID]
    user_client = data["client"]
    
    try:
        await user_client.check_password(password)
        session_string = await user_client.export_session_string()
        await finalize_login(user_client, session_string, message)
    except Exception as e:
        await message.reply_text(f"❌ رمز عبور اشتباه است یا خطایی رخ داد: {e}")


# نهایی کردن و ذخیره اکانت متصل شده
async def finalize_login(user_client, session_string, message):
    # تنظیم هندلر استخراج آیدی (فقط روی اولین اکانت یا تمام اکانت‌هایی که پیام می‌بینند فعال می‌شود)
    @user_client.on_message(filters.group)
    async def collect_only(c: Client, msg: Message):
        user = msg.from_user
        if user and not user.is_bot and user.id not in collected_users:
            collected_users.add(user.id)

    accounts.append(user_client)
    me = await user_client.get_me()
    
    if ADMIN_ID in temp_login_data:
        del temp_login_data[ADMIN_ID]
        
    await message.reply_text(
        f"✅ اکانت **{me.first_name}** (`{me.id}`) با موفقیت متصل شد!\n"
        f"👥 تعداد کل اکانت‌های متصل: `{len(accounts)}`"
    )


# 4️⃣ فقط اولین اکانت وارد گروه هدف می‌شود و آیدی جمع می‌کند
@bot.on_message(filters.command("join"))
async def join_group(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID: return
    if not accounts:
        return await message.reply_text("❌ اول باید حداقل یک اکانت اضافه کنید.")
    
    try:
        link = message.text.split(" ", 1)[1]
        # فقط اکانت اول (اندیس 0) وارد گروه می‌شود
        first_acc = accounts[0]
        chat = await first_acc.join_chat(link)
        
        await message.reply_text(
            f"✅ اولین اکانت با موفقیت وارد گروه **{chat.title}** شد.\n"
            f"مخفیانه در حال جمع‌آوری آیدی کاربران فعال است..."
        )
    except Exception as e:
        await message.reply_text(f"❌ خطا در ورود به گروه: {e}")


# 5️⃣ ارسال پیام به آیدی‌های جمع‌آوری شده (با تقسیم کار بین تمام اکانت‌ها)
@bot.on_message(filters.command("send_all"))
async def send_to_all(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID: return
    if not accounts or not collected_users:
        return await message.reply_text("❌ اکانت یا آیدی‌ای برای ارسال وجود ندارد.")
    
    try:
        ad_text = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text("❌ لطفاً متن خود را بنویسید. مثال:\n`/send_all متن تبلیغاتی...`")

    await message.reply_text(f"🚀 تقسیم کار بین {len(accounts)} اکانت و شروع ارسال به {len(collected_users)} نفر...")
    
    users_list = list(collected_users)
    total_users = len(users_list)
    chunk_size = max(1, total_users // len(accounts))
    account_chunks = [users_list[i:i + chunk_size] for i in range(0, total_users, chunk_size)]

    async def process_account_queue(acc_index, acc, target_users):
        success = 0
        failed = 0
        for user_id in target_users:
            try:
                await acc.send_message(user_id, ad_text)
                success += 1
                await asyncio.sleep(4)  # وقفه امنیتی برای جلوگیری از ریپورت
            except Exception:
                failed += 1
                continue
        await bot.send_message(ADMIN_ID, f"📊 گزارش اکانت شماره `{acc_index + 1}`:\n✅ موفق: {success}\n❌ ناموفق: {failed}")

    tasks = [process_account_queue(i, accounts[i], account_chunks[i]) for i in range(min(len(accounts), len(account_chunks)))]
    await asyncio.gather(*tasks)
    await message.reply_text("🏁 عملیات ارسال به پایان رسید.")


# 6️⃣ مشاهده آمار
@bot.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.reply_text(
        f"📊 **آمار ربات شما:**\n"
        f"👥 اکانت‌های فعال متصل: `{len(accounts)}`\n"
        f"🎯 آیدی‌های جمع‌آوری شده: `{len(collected_users)}` نفر"
    )


bot.run()
