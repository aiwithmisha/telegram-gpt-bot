# Trigger redeploy to force Nixpacks to apply
import os
import json
import openai
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

print(f"📦 python-telegram-bot version: {telegram.__version__}", flush=True)

# Загружаем API-ключи из переменных окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
openai.api_key = OPENAI_API_KEY

# Файл для хранения памяти
MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# 🚀 Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Функция start вызвана", flush=True)
    await update.message.reply_text("Привет! Я персональный помощник. Напиши что-нибудь.")

# 💬 Обработчик обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📥 handle_message вызван", flush=True)
    user_message = update.message.text
    memory = load_memory()
    memory.append({"role": "user", "content": user_message})

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты персональный помощник."},
                *memory
            ],
            temperature=0.5
        )
        reply = response.choices[0].message.content
        memory.append({"role": "assistant", "content": reply})
        save_memory(memory)
        await update.message.reply_text(reply)
    except Exception as e:
        error_text = f"❌ Ошибка от OpenAI: {type(e).__name__} — {e}"
        print(error_text, flush=True)
        await update.message.reply_text("Произошла ошибка при обращении к OpenAI.")
    
if __name__ == "__main__":
    print("👀 Бот запускается...", flush=True)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("⚙️ Запускаем polling...", flush=True)
    app.run_polling()
