import os
from pyrogram import Client, filters
from pyrogram.types import Message
from google import genai

# خواندن اطلاعات از متغیرهای محیطی هاست یا گیت‌هاب
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

ai_client = genai.Client(api_key=GEMINI_API_KEY)
app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

SYSTEM_INSTRUCTION = """
تو یک دستیار هوشمند در تلگرام هستی. پاسخ‌ها را کوتاه، دوستانه، محترمانه و به زبان فارسی ارسال کن. 
طوری پاسخ بده که انگار صاحب اکانت هستی و پاسخ می‌دهی.
"""

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def handle_private_message(client: Client, message: Message):
    if not message.text:
        return
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message.text,
            config={"system_instruction": SYSTEM_INSTRUCTION},
        )
        await message.reply_text(response.text.strip())
    except Exception as e:
        print(f"خطا: {e}")

if __name__ == "__main__":
    print("یوزربرنامه فعال شد...")
    app.run()
