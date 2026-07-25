import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import requests

# 1. خادم إبقاء الخدمة تعمل
app = Flask('')

@app.route('/')
def home():
    return "Aurora Bot is Alive!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

# 2. إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 3. جلب المفاتيح
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا سندباد المدى! بوت أورورا جاهز ومفعل بالكامل الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # محاولة استخدام Gemini
    if GEMINI_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(user_text)
            if response and response.text:
                await update.message.reply_text(response.text)
                return
        except Exception as e:
            logging.error(f"Gemini Error: {e}")

    # محاولة استخدام DeepSeek
    if DEEPSEEK_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": user_text}]
            }
            res = requests.post("https://api.deepseek.com/chat/completions", json=data, headers=headers, timeout=10)
            if res.status_code == 200:
                reply = res.json()['choices'][0]['message']['content']
                await update.message.reply_text(reply)
                return
        except Exception as e:
            logging.error(f"DeepSeek Error: {e}")

    await update.message.reply_text("عذراً، لم أتمكن من الحصول على إجابة من مفاتيح الذكاء الاصطناعي. يرجى التأكد من إضافة GEMINI_API_KEY في إعدادات Render.")

def main():
    keep_alive()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
