import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
import requests

# 1. خادم وهمي لإبقاء الخدمة تعمل مجاناً على Render
app = Flask('')

@app.route('/')
def home():
    return "Aurora Bot is Running Successfully!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

# 2. إعدادات السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 3. جلب المفاتيح من متغيرات البيئة
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")

# تهيئة Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# 4. أوامر البوت
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا سندباد المدى! بوت أورورا جاهز ومفعل بالكامل الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # المحاولة باستخدام Gemini
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
        return
    except Exception as e:
        logging.error(f"Gemini Error: {e}")

    # المحاولة باستخدام DeepSeek في حال تعثر Gemini
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": user_text}]
        }
        res = requests.post("https://api.deepseek.com/chat/completions", json=data, headers=headers)
        if res.status_code == 200:
            reply = res.json()['choices'][0]['message']['content']
            await update.message.reply_text(reply)
            return
    except Exception as e:
        logging.error(f"DeepSeek Error: {e}")

    await update.message.reply_text("عذراً، حدث خطأ أثناء معالجة الطلب، يرجى المحاولة لاحقاً.")

# 5. تشغيل البوت
def main():
    keep_alive() # تشغيل خادم الويب في الخلفية
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
