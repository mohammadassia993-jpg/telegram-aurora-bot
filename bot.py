import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

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

# 2. جلب المفاتيح
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا سندباد المدى! بوت أورورا جاهز ومفعل بالكامل الآن.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    if not GEMINI_KEY:
        await update.message.reply_text("خطأ: مفتاح GEMINI_API_KEY غير مضاف في Render.")
        return

    try:
        # استخدام الاسم المحدث بدقة لتفادي خطأ 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(user_text)
        
        if response and response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("عذراً، لم أتمكن من استخراج إجابة.")
            
    except Exception as e:
        # إذا حدثت مشكلة بالاسم المحدث، نجرب النموذج القياسي المباشر
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(user_text)
            if response and response.text:
                await update.message.reply_text(response.text)
                return
        except Exception as err:
            await update.message.reply_text(f"خطأ في Gemini: {str(err)}")

def main():
    keep_alive()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
