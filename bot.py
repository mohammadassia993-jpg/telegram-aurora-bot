import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai
from openai import OpenAI
from config import TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, DEEPSEEK_API_KEY

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize AI Clients
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
else:
    gemini_model = None

if DEEPSEEK_API_KEY:
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com"
    )
else:
    deepseek_client = None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if not user_message:
        return

    # Send typing action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    reply_text = "عذراً، لم يتم ضبط مفاتيح الذكاء الاصطناعي بشكل صحيح بعد."

    # Try Gemini First
    if gemini_model:
        try:
            response = gemini_model.generate_content(user_message)
            reply_text = response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            # Fallback to DeepSeek if Gemini fails
            if deepseek_client:
                try:
                    response = deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": user_message}],
                    )
                    reply_text = response.choices[0].message.content
                except Exception as ds_e:
                    logger.error(f"DeepSeek Error: {ds_e}")
                    reply_text = (
                        "حدث خطأ أثناء الاتصال بنماذج الذكاء الاصطناعي حالياً."
                    )
    elif deepseek_client:
        try:
            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": user_message}],
            )
            reply_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek Error: {e}")
            reply_text = "حدث خطأ أثناء الاتصال بنموذج DeepSeek."

    await update.message.reply_text(reply_text)


def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing!")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handle all text messages
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )

    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
