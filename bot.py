import re
import os
import base64
from threading import Thread
from flask import Flask

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 Login password
PASSWORD = "12345"

# 📢 Target channels
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

# =========================
# RUNTIME MEMORY
# =========================

LOGGED_USERS = set()
USER_MODE = {}
USER_FOOTER = {}

# =========================
# FLASK KEEP ALIVE
# =========================

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# =========================
# SAFELINK
# =========================

def generate_safelink(url):
    encoded = base64.b64encode(url.encode()).decode()
    return f"https://bdtyone.blogspot.com/?url={encoded}"

# =========================
# COMMANDS
# =========================

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "❌ Use:\n/login password"
        )
        return

    if context.args[0] == PASSWORD:

        LOGGED_USERS.add(user_id)

        await update.message.reply_text(
            "✅ Login successful!"
        )

    else:

        await update.message.reply_text(
            "❌ Wrong password!"
        )

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    LOGGED_USERS.discard(user_id)

    USER_MODE[user_id] = False

    await update.message.reply_text(
        "🔒 Logged out!"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    USER_MODE[user_id] = True

    await update.message.reply_text(
        "🚀 Safelink mode ON!\n\nNow send any post/link."
    )

async def footer_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    current = USER_FOOTER.get(user_id, "No footer set")

    await update.message.reply_text(
        f"📌 Current footer:\n\n{current}\n\nSend new footer now:"
    )

    USER_MODE[user_id] = "footer_wait"

# =========================
# MESSAGE HANDLER
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message:
        return

    if message.chat.type != "private":
        return

    user_id = update.effective_user.id

    # ❌ ignore non logged users
    if user_id not in LOGGED_USERS:
        return

    text = message.text or message.caption or ""

    # =========================
    # FOOTER EDIT MODE
    # =========================

    if USER_MODE.get(user_id) == "footer_wait":

        USER_FOOTER[user_id] = text

        USER_MODE[user_id] = True

        await message.reply_text(
            "✅ Footer updated successfully!"
        )

        return

    # =========================
    # SAFELINK MODE CHECK
    # =========================

    if not USER_MODE.get(user_id):
        return

    # =========================
    # FIND URLS
    # =========================

    urls = re.findall(r'(https?://\S+)', text)

    if not urls:

        await message.reply_text(
            "❌ No link found!"
        )

        return

    # replace all links
    for url in urls:

        safe = generate_safelink(url)

        text = text.replace(url, safe)

    # =========================
    # ADD FOOTER
    # =========================

    footer = USER_FOOTER.get(user_id, "")

    if footer:
        text += f"\n\n{footer}"

    # =========================
    # SEND TO ALL CHANNELS
    # =========================

    success = 0
    failed = 0

    for chat_id in TARGET_CHATS:

        try:

            # photo post
            if message.photo:

                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=message.photo[-1].file_id,
                    caption=text
                )

            # text post
            else:

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text
                )

            success += 1

            print(f"✅ Sent → {chat_id}")

        except Exception as e:

            failed += 1

            print(f"❌ Failed → {chat_id}")
            print(e)

    # =========================
    # REPORT
    # =========================

    await message.reply_text(
        f"✅ Sent: {success}\n❌ Failed: {failed}"
    )

# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # commands
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("footer_edit", footer_edit))

    # messages
    app.add_handler(
        MessageHandler(
            filters.TEXT | filters.PHOTO,
            handle
        )
    )

    print("🚀 Bot running...")

    app.run_polling()

# =========================
# START
# =========================

Thread(target=run_web).start()

main()
