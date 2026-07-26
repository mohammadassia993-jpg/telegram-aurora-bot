#!/usr/bin/env python3
"""
🤖 Aurora Bot - Telegram AI Bot
Powered by Gemini + DeepSeek
"""
import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional

# === التسجيل ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === استيراد المكتبات ===
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# === الإعدادات ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BOT_MODE = os.getenv("BOT_MODE", "polling")  # polling أو webhook
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

# === التحقق من المفاتيح ===
def validate_config():
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("❌ TELEGRAM_BOT_TOKEN غير موجود!")
    if not GEMINI_API_KEY:
        errors.append("❌ GEMINI_API_KEY غير موجود!")
    if not DEEPSEEK_API_KEY:
        errors.append("❌ DEEPSEEK_API_KEY غير موجود!")
    if BOT_MODE == "webhook" and not WEBHOOK_URL:
        errors.append("❌ WEBHOOK_URL مطلوب في وضع Webhook!")
    return errors

# === خدمة Gemini ===
class GeminiService:
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate(self, prompt: str) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.model.generate_content(prompt)),
                timeout=30
            )
            return response.text.strip() if response and response.text else None
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return None

# === خدمة DeepSeek ===
class DeepSeekService:
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
    
    async def generate(self, prompt: str) -> Optional[str]:
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "أنت مساعد ذكي متخصص. قدم إجابات دقيقة وشاملة."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                ),
                timeout=30
            )
            return response.choices[0].message.content.strip() if response.choices else None
        except Exception as e:
            logger.error(f"DeepSeek Error: {e}")
            return None

# === خدمة AI الهجينة ===
class HybridAIService:
    def __init__(self):
        self.gemini = GeminiService()
        self.deepseek = DeepSeekService()
    
    async def generate(self, prompt: str) -> str:
        logger.info(f"📝 طلب جديد: {prompt[:50]}...")
        
        # إرسال الطلبين بالتوازي
        gemini_task = self.gemini.generate(prompt)
        deepseek_task = self.deepseek.generate(prompt)
        
        gemini_resp, deepseek_resp = await asyncio.gather(
            gemini_task, deepseek_task, return_exceptions=True
        )
        
        gemini_text = gemini_resp if isinstance(gemini_resp, str) else ""
        deepseek_text = deepseek_resp if isinstance(deepseek_resp, str) else ""
        
        # دمج الردود
        if gemini_text and deepseek_text:
            # نختار الأطول كأساس
            if len(deepseek_text) > len(gemini_text):
                primary, secondary = deepseek_text, gemini_text
            else:
                primary, secondary = gemini_text, deepseek_text
            
            return f"🧠 *إجابة شاملة:*\n\n{primary}\n\n💡 *نقاط إضافية:*\n{secondary[:500]}"
        
        elif gemini_text:
            return f"🌟 *الإجابة:*\n\n{gemini_text}"
        elif deepseek_text:
            return f"🔥 *الإجابة:*\n\n{deepseek_text}"
        else:
            return "⚠️ *عذراً، حدث خطأ في الاتصال بالنماذج. يرجى المحاولة.*"

ai_service = HybridAIService()

# === الأزرار التفاعلية ===
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 محادثة ذكية", callback_data="chat"),
         InlineKeyboardButton("🎨 توليد صور", callback_data="image")],
        [InlineKeyboardButton("📝 كتابة محتوى", callback_data="content"),
         InlineKeyboardButton("📚 منتجات رقمية", callback_data="products")],
        [InlineKeyboardButton("💰 محفظتي", callback_data="wallet"),
         InlineKeyboardButton("❓ المساعدة", callback_data="help")]
    ])

# === معالجات الأوامر ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "👋 *مرحباً بك في Aurora Bot!*\n\n"
        "🧠 بوت ذكي يجمع بين:\n"
        "• Google Gemini 🌟\n"
        "• DeepSeek 🔥\n\n"
        "✨ اختر خدمة أو اكتب سؤالك مباشرة!"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=main_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *دليل الاستخدام*\n\n"
        "💬 *اكتب أي سؤال* → إجابة ذكية هجينة\n"
        "🎨 *توليد صور* → وصف الصورة\n"
        "📝 *كتابة محتوى* → اختر النوع\n"
        "📚 *منتجات رقمية* → أنشئ وبيع\n\n"
        "💰 *الدفع:* USDT عبر Binance Pay"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# === معالج الأزرار ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "chat":
        await query.edit_message_text(
            "💬 *وضع المحادثة*\n\nاكتب سؤالك الآن:",
            parse_mode="Markdown"
        )
        context.user_data["mode"] = "chat"
    
    elif data == "image":
        await query.edit_message_text(
            "🎨 *توليد الصور*\n\n📝 اكتب وصف الصورة بالتفصيل:",
            parse_mode="Markdown"
        )
        context.user_data["mode"] = "image"
    
    elif data == "content":
        await query.edit_message_text(
            "📝 *كتابة المحتوى*\n\nاكتب الموضوع:",
            parse_mode="Markdown"
        )
        context.user_data["mode"] = "content"
    
    elif data == "products":
        await query.edit_message_text(
            "📚 *المنتجات الرقمية*\n\nقريباً...",
            parse_mode="Markdown"
        )
    
    elif data == "wallet":
        await query.edit_message_text(
            "💰 *محفظتك*\n\nقريباً...",
            parse_mode="Markdown"
        )
    
    elif data == "help":
        await help_cmd(update, context)
    
    elif data == "back":
        await query.edit_message_text(
            "👋 *مرحباً بك في Aurora Bot!*",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

# === معالج الرسائل ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    mode = context.user_data.get("mode", "chat")
    
    # إرسال حالة الكتابة
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING
    )
    
    processing = await update.message.reply_text("⏳ *جاري المعالجة...*", parse_mode="Markdown")
    
    try:
        if mode == "chat":
            response = await ai_service.generate(user_msg)
        elif mode == "image":
            response = "🎨 *توليد الصور* قيد التطوير...\n\nجرب وصفاً أكثر تفصيلاً لاحقاً!"
            context.user_data["mode"] = "chat"
        elif mode == "content":
            prompt = f"اكتب محتوى احترافي عن: {user_msg}. اجعله شاملاً مع أمثلة عملية."
            response = await ai_service.generate(prompt)
            context.user_data["mode"] = "chat"
        else:
            response = await ai_service.generate(user_msg)
        
        await processing.delete()
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing.delete()
        await update.message.reply_text("⚠️ *حدث خطأ. يرجى المحاولة.*", parse_mode="Markdown")

# === معالج الأخطاء ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("⚠️ خطأ غير متوقع.", parse_mode="Markdown")

# === إعداد المعالجات ===
def setup_app(application: Application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

# === التشغيل ===
async def main():
    # التحقق
    errors = validate_config()
    if errors:
        for e in errors:
            logger.error(e)
        sys.exit(1)
    
    logger.info("✅ الإعدادات صحيحة")
    
    # إنشاء التطبيق
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    setup_app(app)
    
    if BOT_MODE == "webhook":
        # === وضع Webhook (لـ Render) ===
        from fastapi import FastAPI
        from uvicorn import Server, Config
        
        web_app = FastAPI()
        
        @web_app.post("/webhook")
        async def webhook(request):
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.process_update(update)
            return {"ok": True}
        
        @web_app.get("/")
        async def health():
            return {"status": "Aurora Bot is running!", "mode": "webhook"}
        
        @web_app.get("/ping")
        async def ping():
            return {"alive": True, "time": datetime.utcnow().isoformat()}
        
        # إعداد Webhook
        await app.initialize()
        await app.start()
        
        webhook_url = f"{WEBHOOK_URL}/webhook"
        await app.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook: {webhook_url}")
        
        # تشغيل الخادم
        config = Config(app=web_app, host="0.0.0.0", port=PORT)
        server = Server(config)
        await server.serve()
        
    else:
        # === وضع Polling (محلي) ===
        logger.info("🚀 Polling mode...")
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        
        # إبقاء البوت يعمل
        stop_event = asyncio.Event()
        await stop_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 توقف البوت")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
