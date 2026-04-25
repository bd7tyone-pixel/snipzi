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
PASSWORD = "115772"

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

# =========================

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    LOGGED_USERS.discard(user_id)

    USER_MODE[user_id] = False

    await update.message.reply_text(
        "🔒 Logged out!"
    )

# =========================

async def start_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    USER_MODE[user_id] = True

    await update.message.reply_text(
        "🚀 Safelink mode ON!\n\nSend any post/link now."
    )

# =========================

async def off_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    USER_MODE[user_id] = False

    await update.message.reply_text(
        "🛑 Safelink mode OFF!"
    )

# =========================

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

async def footer_show(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    footer = USER_FOOTER.get(user_id, "No footer set")

    await update.message.reply_text(
        f"📌 Current Footer:\n\n{footer}"
    )

# =========================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    mode = USER_MODE.get(user_id)

    if mode == True:
        mode_text = "🟢 ON"
    else:
        mode_text = "🔴 OFF"

    footer = USER_FOOTER.get(user_id, "No footer set")

    text = (
        f"🤖 Bot Status\n\n"
        f"Mode: {mode_text}\n"
        f"Channels: {len(TARGET_CHATS)}\n\n"
        f"Footer:\n{footer}"
    )

    await update.message.reply_text(text)

# =========================

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    text = "📢 Target Channels\n\n"

    for i, chat_id in enumerate(TARGET_CHATS, start=1):
        text += f"{i}. {chat_id}\n"

    await update.message.reply_text(text)

# =========================

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    if not context.args:

        await update.message.reply_text(
            "❌ Use:\n/add_channel -100xxxxxxxxxx"
        )

        return

    try:

        chat_id = int(context.args[0])

        if chat_id in TARGET_CHATS:

            await update.message.reply_text(
                "⚠️ Channel already added!"
            )

            return

        TARGET_CHATS.append(chat_id)

        await update.message.reply_text(
            f"✅ Channel added:\n{chat_id}"
        )

    except:

        await update.message.reply_text(
            "❌ Invalid channel ID!"
        )

# =========================

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in LOGGED_USERS:
        return

    if not context.args:

        await update.message.reply_text(
            "❌ Use:\n/remove_channel -100xxxxxxxxxx"
        )

        return

    try:

        chat_id = int(context.args[0])

        if chat_id not in TARGET_CHATS:

            await update.message.reply_text(
                "⚠️ Channel not found!"
            )

            return

        TARGET_CHATS.remove(chat_id)

        await update.message.reply_text(
            f"✅ Channel removed:\n{chat_id}"
        )

    except:

        await update.message.reply_text(
            "❌ Invalid channel ID!"
        )

# =========================
# MAIN MESSAGE HANDLER
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message:
        return

    # private only
    if message.chat.type != "private":
        return

    user_id = update.effective_user.id

    # only logged users
    if user_id not in LOGGED_USERS:
        return

    text = (
        message.text
        or message.caption
        or ""
    )

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
    # MODE CHECK
    # =========================

    if not USER_MODE.get(user_id):
        return

    # =========================
    # FIND URLS
    # =========================

    urls = re.findall(
        r'https?://[^\s]+',
        text
    )

    if not urls:

        await message.reply_text(
            "❌ No link found!"
        )

        return

    # replace urls
    for url in urls:

        safe = generate_safelink(url)

        text = text.replace(url, safe)

    # =========================
    # FOOTER
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

            # PHOTO
            if message.photo:

                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=message.photo[-1].file_id,
                    caption=text
                )

            # VIDEO
            elif message.video:

                await context.bot.send_video(
                    chat_id=chat_id,
                    video=message.video.file_id,
                    caption=text
                )

            # DOCUMENT
            elif message.document:

                await context.bot.send_document(
                    chat_id=chat_id,
                    document=message.document.file_id,
                    caption=text
                )

            # TEXT
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
    app.add_handler(CommandHandler("on", start_mode))
    app.add_handler(CommandHandler("off", off_mode))
    app.add_handler(CommandHandler("footer_edit", footer_edit))
    app.add_handler(CommandHandler("footer_show", footer_show))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("channels", channels))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))

    # media/text handler
    app.add_handler(
        MessageHandler(
            filters.ALL,
            handle
        )
    )

    print("🚀 Bot running...")

    app.run_polling(
        drop_pending_updates=True
    )

# =========================
# START
# =========================

Thread(target=run_web).start()

main()
