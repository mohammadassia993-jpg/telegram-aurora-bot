import os
import threading
import telebot
from flask import Flask

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 10000))

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(func=lambda m: True)
def handle_any_message(message):
    bot.reply_to(message, "مرحبا 👋 أنا أورورا، وأنا شغالة تمام!")

app = Flask(__name__)

@app.route("/ping")
def ping():
    return "OK", 200

@app.route("/")
def home():
    return "Aurora Bot is alive"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
