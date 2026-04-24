import re
import os
import asyncio
import base64
from collections import deque
from threading import Thread
from flask import Flask
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

POST_DELAY = 60

# 🔁 Queue
task_queue = deque()
channel_index = 0

# 🌐 Flask (keep alive)
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


# 🧠 Worker
async def worker(app):
    global channel_index

    while True:
        if not task_queue:
            await asyncio.sleep(5)
            continue

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

            print(f"✅ Sent → {chat_id}")

        except Exception as e:
            import traceback
            print("❌ ERROR:", e)
            traceback.print_exc()

        await asyncio.sleep(POST_DELAY)


# 📩 Handler
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or message.chat.type != "private":
        return

    user = update.effective_user
    if not user or user.id != OWNER_ID:
        return

    text = message.text or message.caption or ""
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
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle))

    # worker start after loop
    async def on_start(app):
        asyncio.create_task(worker(app))

    app.post_init = on_start

    print("🚀 Bot running...")
    app.run_polling()


# ▶️ Start
Thread(target=run_web).start()
main()
