import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
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


# ---------------- CHECK ADMIN ---------------- #

async def is_admin(update: Update):
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ["administrator", "creator"]


# ---------------- POINT SYSTEM ---------------- #

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    member = await chat.get_member(user.id)
    if member.status in ["administrator", "creator"]:
        return

    duration = None
    points_to_add = 0

    if update.message.voice:
        duration = update.message.voice.duration
        points_to_add = 1

    elif update.message.video:
        duration = update.message.video.duration
        points_to_add = 2

    elif update.message.video_note:
        duration = update.message.video_note.duration
        points_to_add = 2

    else:
        return

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


# ---------------- ADMIN ADDPOINTS ---------------- #

async def addpoints_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("❌ Only admins can use this command.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /addpoints @username amount")
        return

    target_username = context.args[0]
    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("Points must be a number.")
        return

    data = load_data()

    # Find user in database
    for user_id, user_data in data.items():
        if user_data["name"].lower() == target_username.lower():
            user_data["points"] += amount
            save_data(data)
            await update.message.reply_text(
                f"✅ {target_username} now has {user_data['points']} SpeakPoints."
            )
            return

    await update.message.reply_text("User not found in database.")


# ---------------- TEXT COMMANDS ---------------- #

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.lower()

    data = load_data()
    user_id = str(user.id)

    if text == "speakpoints":
        points = data.get(user_id, {}).get("points", 0)
        await update.message.reply_text(
            f"📊 {user.first_name}, you currently have:\n\n"
            f"🔥 {points} SpeakPoints"
        )

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

    app.add_handler(CommandHandler("addpoints", addpoints_command))

    print("SpeakPoint Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
