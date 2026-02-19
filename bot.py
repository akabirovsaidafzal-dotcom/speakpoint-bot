import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")

DATA_FILE = "speakpoints.json"


# ---------------- DATA FUNCTIONS ---------------- #

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# ---------------- POINT SYSTEM ---------------- #

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # 🚫 Skip admins and owner
    member = await chat.get_member(user.id)
    if member.status in ["administrator", "creator"]:
        return

    duration = None
    points_to_add = 0

    # 🎤 Voice
    if update.message.voice:
        duration = update.message.voice.duration
        points_to_add = 1

    # 🎥 Video
    elif update.message.video:
        duration = update.message.video.duration
        points_to_add = 2

    # 🎥 Video Note
    elif update.message.video_note:
        duration = update.message.video_note.duration
        points_to_add = 2

    else:
        return

    # ⏳ Duration check
    if duration < 20:
        await update.message.reply_text(
            f"🌟 Dear {user.first_name}, your answer is great!\n\n"
            "But your voice or video must be at least 20 seconds ⏳\n"
            "Please expand your answer a little more 💬✨\n\n"
            "You can do it! 💪🔥"
        )
        return

    data = load_data()
    user_id = str(user.id)

    username = f"@{user.username}" if user.username else user.first_name

    if user_id not in data:
        data[user_id] = {"name": username, "points": 0}

    data[user_id]["name"] = username
    data[user_id]["points"] += points_to_add

    save_data(data)

    await update.message.reply_text(
        f"👏 Very nice, {username}!\n"
        f"🔥 +{points_to_add} SpeakPoint{'s' if points_to_add > 1 else ''}\n"
        f"📊 Total: {data[user_id]['points']}"
    )


# ---------------- TEXT COMMANDS ---------------- #

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.lower()

    data = load_data()
    user_id = str(user.id)

    # Personal points
    if text == "speakpoints":
        if user_id in data:
            points = data[user_id]["points"]
        else:
            points = 0

        await update.message.reply_text(
            f"📊 {user.first_name}, you currently have:\n\n"
            f"🔥 {points} SpeakPoints"
        )

    # Leaderboard
    elif text == "top":
        if not data:
            await update.message.reply_text("No SpeakPoints yet 🚀")
            return

        sorted_users = sorted(
            data.values(),
            key=lambda x: x["points"],
            reverse=True
        )

        leaderboard = "🏆 LEADERBOARD 🏆\n\n"
        medals = ["🥇", "🥈", "🥉"]

        for i, user_data in enumerate(sorted_users[:10], start=1):
            if i <= 3:
                leaderboard += f"{medals[i-1]} {user_data['name']} - {user_data['points']} SpeakPoints\n"
            else:
                leaderboard += f"{i}. {user_data['name']} - {user_data['points']} SpeakPoints\n"

        await update.message.reply_text(leaderboard)


# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.VOICE, process_message))
    app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, process_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("SpeakPoint Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
