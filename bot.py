import os, sys, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
BOT_MODE = os.getenv("BOT_MODE", "webhook")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "10000"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    async def generate(self, prompt):
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(loop.run_in_executor(None, lambda: self.model.generate_content(prompt)), timeout=30)
            return response.text.strip() if response and response.text else None
        except: return None

class DeepSeekService:
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com/v1")
    async def generate(self, prompt):
        try:
            response = await asyncio.wait_for(self.client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], temperature=0.7, max_tokens=2000), timeout=30)
            return response.choices[0].message.content.strip() if response.choices else None
        except: return None

class HybridAI:
    def __init__(self):
        self.gemini = GeminiService()
        self.deepseek = DeepSeekService()
    async def generate(self, prompt):
        g, d = await asyncio.gather(self.gemini.generate(prompt), self.deepseek.generate(prompt), return_exceptions=True)
        g = g if isinstance(g, str) else ""
        d = d if isinstance(d, str) else ""
        if g and d:
            if len(d) > len(g): return f"🧠 *إجابة شاملة:*\n\n{d}\n\n💡 *إضافي:*\n{g[:500]}"
            return f"🧠 *إجابة شاملة:*\n\n{g}\n\n💡 *إضافي:*\n{d[:500]}"
        elif g: return f"🌟 *الإجابة:*\n\n{g}"
        elif d: return f"🔥 *الإجابة:*\n\n{d}"
        return "⚠️ خطأ في الاتصال"

ai = HybridAI()

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 محادثة", callback_data="chat"), InlineKeyboardButton("🎨 صور", callback_data="img")],
        [InlineKeyboardButton("📝 محتوى", callback_data="content"), InlineKeyboardButton("❓ مساعدة", callback_data="help")]
    ])

async def start(update, context):
    await update.message.reply_text("👋 *Aurora Bot*\n🧠 Gemini + DeepSeek\n\nاختر خدمة:", parse_mode="Markdown", reply_markup=menu())

async def help_cmd(update, context):
    await update.message.reply_text("📖 اكتب سؤالك مباشرة أو اختر من القائمة", parse_mode="Markdown")

async def button(update, context):
    q = update.callback_query
    await q.answer()
    if q.data == "chat": await q.edit_message_text("💬 اكتب سؤالك:", parse_mode="Markdown"); context.user_data["mode"] = "chat"
    elif q.data == "img": await q.edit_message_text("🎨 قريباً...", parse_mode="Markdown")
    elif q.data == "content": await q.edit_message_text("📝 اكتب الموضوع:", parse_mode="Markdown"); context.user_data["mode"] = "content"
    elif q.data == "help": await help_cmd(update, context)

async def msg(update, context):
    m = update.message.text
    p = await update.message.reply_text("⏳...", parse_mode="Markdown")
    try:
        mode = context.user_data.get("mode", "chat")
        if mode == "content": r = await ai.generate(f"اكتب محتوى احترافي عن: {m}"); context.user_data["mode"] = "chat"
        else: r = await ai.generate(m)
        await p.delete()
        await update.message.reply_text(r, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await p.delete()
        await update.message.reply_text("⚠️ خطأ", parse_mode="Markdown")

async def main():
    if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY or not DEEPSEEK_API_KEY:
        logger.error("مفاتيح ناقصة"); sys.exit(1)
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    
    if BOT_MODE == "webhook":
        from fastapi import FastAPI
        from uvicorn import Server, Config
        web = FastAPI()
        @web.post("/webhook")
        async def wh(request):
            data = await request.json()
            await app.process_update(Update.de_json(data, app.bot))
            return {"ok": True}
        @web.get("/")
        async def root(): return {"status": "ok"}
        @web.get("/ping")
        async def ping(): return {"alive": True}
        await app.initialize()
        await app.start()
        await app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
        await Server(Config(app=web, host="0.0.0.0", port=PORT)).serve()
    else:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
    except Exception as e: logger.error(f"Fatal: {e}"); sys.exit(1)
