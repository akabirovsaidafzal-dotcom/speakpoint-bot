import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

import os

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")


DATA_FILE = "speakpoints.json"

async def get_chat_id(update, context):
    await update.message.reply_text(str(update.effective_chat.id))

# ------------------ DATABASE ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def add_user(user_id, username):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {
            "username": username,
            "points": 0
        }
    save_data(data)


def add_points(user_id, amount):
    data = load_data()
    if str(user_id) in data:
        data[str(user_id)]["points"] += amount
        save_data(data)


# ------------------ HANDLERS ------------------

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # 🚫 Skip if admin or owner
    member = await chat.get_member(user.id)
    if member.status in ["administrator", "creator"]:
        return

    data = load_data()

    user_id = str(user.id)
    data[user_id] = data.get(user_id, 0) + 5

    save_data(data)

    await update.message.reply_text(
        f"🎤 +5 SpeakPoints, {user.first_name}!\n"
        f"Total: {data[user_id]} points"
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # 🚫 Skip if admin or owner
    member = await chat.get_member(user.id)
    if member.status in ["administrator", "creator"]:
        return

    data = load_data()

    user_id = str(user.id)
    data[user_id] = data.get(user_id, 0) + 5

    save_data(data)

    await update.message.reply_text(
        f"📹 +5 SpeakPoints, {user.first_name}!\n"
        f"Total: {data[user_id]} points"
    )


async def show_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()

    if str(user.id) not in data:
        await update.message.reply_text("You have 0 SpeakPoints.")
        return

    points = data[str(user.id)]["points"]
    await update.message.reply_text(
        f"🏆 @{user.username or user.first_name}, you have {points} SpeakPoints."
    )


async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    if not data:
        await update.message.reply_text("No SpeakPoints yet.")
        return

    leaderboard = sorted(
        data.values(),
        key=lambda x: x["points"],
        reverse=True
    )

    text = "🏆 Leaderboard:\n\n"
    for i, user in enumerate(leaderboard, start=1):
        text += f"{i}. @{user['username']} — {user['points']} SpeakPoints\n"

    await update.message.reply_text(text)


async def handle_video_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # 🚫 Skip if admin or owner
    member = await chat.get_member(user.id)
    if member.status in ["administrator", "creator"]:
        return

    data = load_data()

    user_id = str(user.id)
    data[user_id] = data.get(user_id, 0) + 5

    save_data(data)

    await context.bot.send_message(
        chat_id=chat.id,
        text=f"🎥 +5 SpeakPoints for starting video chat, {user.first_name}!\n"
             f"Total: {data[user_id]} points"
    )

# ------------------ MAIN ------------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("id", get_chat_id))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, handle_video))
    app.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_STARTED, handle_video_chat))

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^speakpoints$"), show_points))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^top$"), show_top))

    print("SpeakPoint Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
