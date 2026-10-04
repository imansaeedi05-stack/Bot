from flask import Flask
from pyrogram import Client
from pytgcalls import PyTgCalls
import asyncio
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# خواندن اطلاعات از تنظیمات رندر (Environmental Variables)
api_id = int(os.getenv("API_ID", "38859635"))
api_hash = os.getenv("API_HASH", "5232c81647167a853b97fcadf68ea9d2")
string_session = os.getenv("STRING_SESSION", "your_string_session")

bot = Client(
    "my_bot",
    api_id=api_id,
    api_hash=api_hash,
    session_string=string_session
)

call_py = PyTgCalls(bot)

async def main():
    await bot.start()
    await call_py.start()
    print("Bot and PyTgCalls started successfully!")

if __name__ == "__main__":
    import threading
    def run_flask():
        app.run(host="0.0.0.0", port=10000)
    
    t = threading.Thread(target=run_flask)
    t.start()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
