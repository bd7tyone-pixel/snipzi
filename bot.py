import re
import os
import asyncio
from collections import deque
from flask import Flask
from threading import Thread
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 🔑 ENV
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8291579707

# 📢 Channels
TARGET_CHATS = [
    -1003562574974,
    -1003904302343,
    -1003365014481,
    -1003975618059,
    -1003783765145,
    -1003996688648,
    -1003615140429,
    -1003930491160,
    -1003909969755,
    -1003760895908,
    -1003780741445,
    -1003779541404,
    -1003871435498
]

POST_DELAY = 60  # seconds gap

# 🔁 Queue system
task_queue = deque()
channel_index = 0

# 🌐 Flask server (Render fix)
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)


# 🔗 Safelink
def generate_safelink(url):
    encoded = base64.b64encode(url.encode()).decode()
    return f"https://bdtyone.blogspot.com/?url={encoded}"


# 🧠 Worker (background sender)
async def worker(app):
    global channel_index

    while True:
        if task_queue:
            data = task_queue.popleft()

            chat_id = TARGET_CHATS[channel_index]
            channel_index = (channel_index + 1) % len(TARGET_CHATS)

            try:
                if data["photo"]:
                    await app.bot.send_photo(
                        chat_id=chat_id,
                        photo=data["photo"],
                        caption=data["text"]
                    )
                else:
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=data["text"]
                    )

                print(f"✅ Sent to {chat_id}")

            except Exception as e:
                print("❌ ERROR:", e)

            await asyncio.sleep(POST_DELAY)

        else:
            await asyncio.sleep(5)


# 📩 Handler
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or message.chat.type != "private":
        return

    user = update.effective_user
    if not user or user.id != OWNER_ID:
        return

    text = message.text or message.caption
    if not text:
        return

    urls = re.findall(r'(https?://\S+)', text)
    if not urls:
        return

    for url in urls:
        safe = generate_safelink(url)
        new_text = text.replace(url, safe)

        task_queue.append({
            "text": new_text,
            "photo": message.photo[-1].file_id if message.photo else None
        })

    await message.reply_text(f"✅ {len(urls)} link queued!")


# 🚀 Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle))

    # 🔥 background worker start
    asyncio.create_task(worker(app))

    print("🚀 Bot running...")
    await app.run_polling()


# 🌐 Start Flask thread
Thread(target=run_web).start()

# ▶️ Run bot
asyncio.run(main())
