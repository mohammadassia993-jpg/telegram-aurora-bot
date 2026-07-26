import os
import logging
from flask import Flask
from threading import Thread
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد التسجيل للمتابعة في Render Logs
logging.basicConfig(level=logging.INFO)

# --- 1. خادم Flask لاستقبال الهيلث تشيك وتفادي خطأ HTTP 502 ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Aurora Bot is Alive and Running!", 200

def run_flask():
    # Render يحدد المنفذ تلقائياً عبر متغير البيئة PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- 2. إعدادات المفاتيح وعميل Gemini الرسمية الحديثة ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# تهيئة العميل بـ google-genai الحديثة
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 3. دالة استدعاء الموديل المعتمد ---
def ask_gemini(prompt_text: str) -> str:
    try:
        # استخدام الموديل المستقر المعتمد حالياً
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text,
        )
        return response.text
    except Exception as e:
        logging.error(f"Gemini Error: {e}")
        return f"حدث خطأ أثناء التواصل مع الذكاء الاصطناعي: {e}"

# --- 4. معالجات التليجرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا سندباد المدى! البوت يعمل الآن بنجاح وجاهز لخدمتك.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    
    reply = ask_gemini(user_text)
    
    # تقسيم الرسالة إذا تجاوزت حد تليجرام
    if len(reply) > 4000:
        for i in range(0, len(reply), 4000):
            await update.message.reply_text(reply[i:i + 4000])
    else:
        await update.message.reply_text(reply)

# --- 5. التشغيل الرئيسي ---
def main():
    # تشغيل Flask في Thread مستقل قبل بدء البوت
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    # تشغيل بوت تليجرام
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Starting Telegram Bot Polling...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
