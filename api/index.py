from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import os
import yt_dlp
import json

# === CONFIG ===
TOKEN = "7544666074:AAHHb6mGPC_XHFV_qA9ENFUqTe8Bbb5wkK0"
REQUIRED_CHANNEL = "@SohilScripter"
ADMIN_ID = 6411315434  # Replace with your Telegram user ID
USER_DB = "users.json"

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# === Helpers ===
def load_users():
    if not os.path.exists(USER_DB): return []
    with open(USER_DB, "r") as f:
        return json.load(f)

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USER_DB, "w") as f:
            json.dump(users, f)

def is_user_joined(chat_member):
    return chat_member.status in ['member', 'administrator', 'creator']

# === /start ===
def start(update, context):
    user_id = update.effective_user.id
    save_user(user_id)

    chat_member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
    if not is_user_joined(chat_member):
        join_btn = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")]
        ])
        update.message.reply_text(
            "🚫 *Access Denied!*\n\nJoin our channel to use this bot.",
            reply_markup=join_btn,
            parse_mode=telegram.ParseMode.MARKDOWN
        )
        return

    update.message.reply_text(
        "👋 *Welcome!*\n\nSend an Instagram reel/post link, I’ll fetch it for you! 📥",
        parse_mode=telegram.ParseMode.MARKDOWN
    )

# === Instagram Handler ===
def download_reel(update, context):
    user_id = update.effective_user.id
    save_user(user_id)

    chat_member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
    if not is_user_joined(chat_member):
        update.message.reply_text("🚫 Please join our channel first. Use /start")
        return

    url = update.message.text
    if "instagram.com" not in url:
        update.message.reply_text("❗️Please send a valid Instagram URL.")
        return

    file_name = "reel.mp4"
    ydl_opts = {
        'outtmpl': file_name,
        'format': 'mp4',
        'quiet': True
    }

    try:
        update.message.reply_text("⏳ Downloading reel...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        update.message.reply_video(
            video=open(file_name, 'rb'),
            caption="✅ Reel downloaded!\n\n_by @SohilCodes_",
            parse_mode=telegram.ParseMode.MARKDOWN
        )
    except Exception:
        update.message.reply_text("⚠️ Failed to download. Reel may be private or invalid.")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

# === Broadcast (admin only) ===
def broadcast(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ You're not authorized to use this command.")
        return

    if len(context.args) == 0:
        update.message.reply_text("❗️Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    users = load_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(chat_id=uid, text=message)
            success += 1
        except:
            continue
    update.message.reply_text(f"✅ Broadcast sent to {success} users.")

# === Stats ===
def stats(update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ Only admin can use this.")
        return

    total = len(load_users())
    update.message.reply_text(f"📊 Total users: *{total}*", parse_mode=telegram.ParseMode.MARKDOWN)

# === Webhook ===
@app.route("/", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# === Handlers ===
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("broadcast", broadcast, pass_args=True))
dispatcher.add_handler(CommandHandler("stats", stats))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_reel))
