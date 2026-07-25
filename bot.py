import os
import requests
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. خادم ويب لتخطي إغلاق Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Aurora Bot is Running Smoothly!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web, daemon=True).start()

# --- 2. إعدادات المفاتيح ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- 3. الاتصال المباشر بـ Gemini REST API ---
def ask_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        res_data = response.json()
        
        if response.status_code == 200:
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            err_msg = res_data.get("error", {}).get("message", "خطأ غير معروف")
            return f"خطأ من جوجل ({response.status_code}): {err_msg}"
    except Exception as e:
        return f"خطأ في الاتصال: {e}"

# --- 4. معالجات التليجرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك يا سندباد المدى! أنا جاهز ومفعل الآن لإجابة كافة استفساراتك.")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action("typing")
    
    answer = ask_gemini(user_text)
    
    if len(answer) > 4000:
        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i + 4000])
    else:
        await update.message.reply_text(answer)

# --- 5. التشغيل الرئيسي ---
def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    print("Bot is polling...")
    # هذه الخاصية تمسح أي رسائل علقت سابقاً وتنعش البوت فوراً
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
