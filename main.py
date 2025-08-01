# Trigger redeploy to force Nixpacks to apply
import os
import asyncio
import nest_asyncio
nest_asyncio.apply()
import json
import openai
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

print(f"📦 python-telegram-bot version: {telegram.__version__}")  # <--- добавили

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        error_text = f"❌ Ошибка при обращении к OpenAI: {type(e).__name__} — {e}"
        await update.message.reply_text(error_text)

# 👇 Новая функция для обработки голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    ogg_path = "voice.ogg"
    mp3_path = "voice.mp3"

    await file.download_to_drive(ogg_path)

    try:
        subprocess.run(["ffmpeg", "-i", ogg_path, mp3_path], check=True)
    except subprocess.CalledProcessError:
        await update.message.reply_text("Ошибка при конвертации голосового сообщения.")
        return

    with open(mp3_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)

    question = transcript["text"]
    await update.message.reply_text(f"🗣 Распознано:\n{question}")

    messages = [{"role": "user", "content": question}]
    completion = openai.ChatCompletion.create(model="gpt-4o", messages=messages)
    answer = completion.choices[0].message["content"]
    await update.message.reply_text(answer)

    os.remove(ogg_path)
    os.remove(mp3_path)

# 🚀 Функция старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я готов к работе. Напиши мне что-нибудь.")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("🚀 Бот запущен и работает через webhook...")

    PORT = int(os.environ.get("PORT", 8443))
    URL = os.environ.get("RAILWAY_STATIC_URL")

    if not URL:
        print("❌ Ошибка: переменная RAILWAY_STATIC_URL не найдена.")
        exit(1)

    await app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=f"{URL}/webhook"
)

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
