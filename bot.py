    main()
import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# 1. خادم إبقاء الخدمة تعمل على Render
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

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا سندباد المدى! بوت أورورا جاهز ومفعل بالكامل الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if not GEMINI_KEY:
        await update.message.reply_text("خطأ: مفتاح GEMINI_API_KEY غير مضاف في إعدادات Render.")
        return

    # الاتصال المباشر بـ Gemini REST API لضمان استقرار الخدمة
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": user_text}]
        }]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        res_data = response.json()

        if response.status_code == 200:
            try:
                reply_text = res_data['candidates'][0]['content']['parts'][0]['text']
                await update.message.reply_text(reply_text)
            except (KeyError, IndexError):
                await update.message.reply_text("تم استلام الاستجابة ولكن تعذر استخراج النص منها.")
        else:
            error_msg = res_data.get('error', {}).get('message', 'خطأ غير معروف')
            await update.message.reply_text(f"خطأ من جوجل (كود {response.status_code}):\n{error_msg}")

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ في الاتصال الشبكي:\n{str(e)}")

def main():
    keep_alive()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
