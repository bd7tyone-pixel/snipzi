import re
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os


BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8291579707  # তোমার ID (log থেকে দেখলাম)

# 👉 এখানে তোমার real channel ID বসাও
TARGET_CHATS = [
    -1003779541404, # chicks
    -1003871435498
]

def generate_safelink(url):
    return f"https://snipzi.blogspot.com/p/safelink-generator.html?url={url}"

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("\n📩 New Update Received")

    message = update.message
    if not message:
        print("❌ No message found")
        return

    print("👤 Chat type:", message.chat.type)
    print("👤 User ID:", update.effective_user.id if update.effective_user else "None")

    # 👉 শুধু private chat allow
    if message.chat.type != "private":
        print("❌ Not private chat")
        return

    # 👉 owner check
    user = update.effective_user
    if not user or user.id != OWNER_ID:
        print("❌ Not owner")
        return

    text = message.text or message.caption
    if not text:
        print("❌ No text")
        return

    print("📝 Message:", text)

    urls = re.findall(r'(https?://\S+)', text)
    if not urls:
        print("❌ No URL found")
        return

    original = urls[0]
    safe = generate_safelink(original)
    new_text = text.replace(original, safe)

    print("🔗 Original:", original)
    print("🔐 Safelink:", safe)
    print("📤 Sending to:", TARGET_CHATS)

    try:
        # 📸 photo case
        if message.photo:
            photo = message.photo[-1].file_id

            for chat in TARGET_CHATS:
                print(f"➡️ Sending photo to {chat}")
                await context.bot.send_photo(
                    chat_id=chat,
                    photo=photo,
                    caption=new_text
                )

        # 📝 text case
        else:
            for chat in TARGET_CHATS:
                print(f"➡️ Sending text to {chat}")
                await context.bot.send_message(
                    chat_id=chat,
                    text=new_text
                )

        print("✅ Message sent successfully!")

    except Exception as e:
        print("❌ ERROR:", e)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle))

print("🚀 Bot is running...")
app.run_polling()
