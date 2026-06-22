"""
🇧🇷 Бот-репетитор бразильского португальского
Версия 3 — ИСПРАВЛЕННАЯ для Railway webhook

Требует: pip install python-telegram-bot anthropic flask gunicorn
"""

import os
import json
import asyncio
import threading
from pathlib import Path
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from flask import Flask, request

# ═══════════════════════════════════════════════════════════
# КОНФИГ
# ═══════════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", 8080))

if not TELEGRAM_TOKEN or not ANTHROPIC_API_KEY:
    print("⚠️  ОШИБКА: Установи TELEGRAM_TOKEN и ANTHROPIC_API_KEY!")
    exit(1)

client = Anthropic(api_key=ANTHROPIC_API_KEY)
MEMORY_FILE = "user_memory.json"

SYSTEM_PROMPT = """Você é um professor de português brasileiro para um estudante russo de nível iniciante.

Regras:
1. Sempre responda em RUSSO, mas use exemplos em português do Brasil
2. Explique as diferenças entre o português europeu e brasileiro quando relevante
3. Use transliteração em cirílico para palavras difíceis: obrigado [обригáду]
4. Corrija erros com gentileza — primeiro elogie, depois corrija
5. Use exemplos do cotidiano brasileiro (comida, música, praias, futebol)
6. Adapte ao nível iniciante: vocabulário simples, frases curtas

Para /vocab — dê 5 palavras novas com: palavra, transcrição, tradução, exemplo
Para /grammar — explique uma regra gramatical com 3 exemplos práticos  
Para /chat — converse naturalmente, corrija com suavidade
Para /quiz — faça 5 perguntas (escolha múltipla ou tradução)

Seja animado, use emojis, torne o aprendizado divertido! 🎉"""


# ═══════════════════════════════════════════════════════════
# ПАМЯТЬ
# ═══════════════════════════════════════════════════════════

def load_memory():
    if Path(MEMORY_FILE).exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_data(user_id: str):
    memory = load_memory()
    if user_id not in memory:
        memory[user_id] = {"history": [], "words_learned": 0, "sessions": 0}
        save_memory(memory)
    return memory[user_id]


def save_user_data(user_id: str, user_data: dict):
    memory = load_memory()
    memory[user_id] = user_data
    save_memory(memory)


def add_to_history(user_id: str, role: str, content: str):
    user_data = get_user_data(user_id)
    user_data["history"].append({"role": role, "content": content})
    if len(user_data["history"]) > 50:
        user_data["history"] = user_data["history"][-50:]
    save_user_data(user_id, user_data)


def ask_claude(user_id: str, user_message: str) -> str:
    """СИНХРОННАЯ версия (без async) — работает в Flask"""
    user_data = get_user_data(user_id)
    add_to_history(user_id, "user", user_message)

    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=user_data["history"]
        )

        reply = response.content[0].text
        add_to_history(user_id, "assistant", reply)
        print(f"✅ Claude ответил пользователю {user_id}")
        return reply
    
    except Exception as e:
        error_msg = f"❌ Ошибка Claude API: {str(e)}"
        print(f"ERROR: {error_msg}")
        return error_msg


# ═══════════════════════════════════════════════════════════
# КОМАНДЫ (СИНХРОННЫЕ)
# ═══════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    user_data["sessions"] += 1
    save_user_data(user_id, user_data)

    keyboard = [
        [InlineKeyboardButton("📚 Слова дня", callback_data="vocab"),
         InlineKeyboardButton("📝 Грамматика", callback_data="grammar")],
        [InlineKeyboardButton("💬 Разговор", callback_data="chat"),
         InlineKeyboardButton("🎯 Квиз", callback_data="quiz")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🇧🇷 *Olá! Bem-vindo!* [Олá! Бэм-виндо!]\n\n"
        "Я твой персональный репетитор бразильского португальского!\n\n"
        "Выбери что хочешь поучить сегодня:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def vocab_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await update.message.reply_text("⏳ Подбираю слова для тебя...")
    
    reply = ask_claude(user_id, "/vocab — дай 5 новых слов на тему повседневной жизни")
    
    user_data = get_user_data(user_id)
    user_data["words_learned"] += 5
    save_user_data(user_id, user_data)
    
    await update.message.reply_text(reply, parse_mode="Markdown")


async def grammar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await update.message.reply_text("⏳ Готовлю урок грамматики...")
    
    reply = ask_claude(user_id, "/grammar — объясни важное правило для новичка")
    await update.message.reply_text(reply, parse_mode="Markdown")


async def chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    reply = ask_claude(user_id, "/chat — начни диалог на португальском для новичка")
    await update.message.reply_text(reply, parse_mode="Markdown")


async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await update.message.reply_text("⏳ Составляю квиз...")
    reply = ask_claude(user_id, "/quiz — тест из 5 вопросов")
    await update.message.reply_text(reply, parse_mode="Markdown")


async def progress_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = get_user_data(user_id)
    
    words = user_data.get("words_learned", 0)
    sessions = user_data.get("sessions", 0)
    msgs = len(user_data.get("history", []))
    
    await update.message.reply_text(
        f"📊 *Твой прогресс*\n\n"
        f"📚 Слов изучено: {words}\n"
        f"🎯 Сессий: {sessions}\n"
        f"💬 Сообщений: {msgs}\n\n"
        f"_Bora estudar! 🇧🇷_",
        parse_mode="Markdown"
    )


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    memory = load_memory()
    if user_id in memory:
        memory[user_id]["history"] = []
        save_memory(memory)
    await update.message.reply_text("🔄 История очищена!")


# ═══════════════════════════════════════════════════════════
# ОБРАБОТКА КНОПОК И СООБЩЕНИЙ
# ═══════════════════════════════════════════════════════════

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data

    if data == "vocab":
        await query.message.reply_text("⏳ Подбираю слова...")
        reply = ask_claude(user_id, "/vocab — 5 полезных слов")
        user_data = get_user_data(user_id)
        user_data["words_learned"] += 5
        save_user_data(user_id, user_data)
        await query.message.reply_text(reply, parse_mode="Markdown")
    elif data == "grammar":
        await query.message.reply_text("⏳ Готовлю урок...")
        reply = ask_claude(user_id, "/grammar — объясни правило")
        await query.message.reply_text(reply, parse_mode="Markdown")
    elif data == "chat":
        reply = ask_claude(user_id, "/chat — диалог для практики")
        await query.message.reply_text(reply, parse_mode="Markdown")
    elif data == "quiz":
        await query.message.reply_text("⏳ Составляю квиз...")
        reply = ask_claude(user_id, "/quiz — тест")
        await query.message.reply_text(reply, parse_mode="Markdown")
    elif data == "progress":
        user_data = get_user_data(user_id)
        await query.message.reply_text(
            f"📊 Слов: {user_data.get('words_learned', 0)} | "
            f"Сессий: {user_data.get('sessions', 0)}",
            parse_mode="Markdown"
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )
    
    reply = ask_claude(user_id, text)
    await update.message.reply_text(reply, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════
# FLASK + WEBHOOK
# ═══════════════════════════════════════════════════════════

app = Flask(__name__)
application = None
loop = None


def init_bot_sync():
    """Инициализирует бота (один раз)"""
    global application, loop
    
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if application is None:
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("vocab", vocab_cmd))
        application.add_handler(CommandHandler("grammar", grammar_cmd))
        application.add_handler(CommandHandler("chat", chat_cmd))
        application.add_handler(CommandHandler("quiz", quiz_cmd))
        application.add_handler(CommandHandler("progress", progress_cmd))
        application.add_handler(CommandHandler("reset", reset_cmd))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint — обрабатывает сообщения от Telegram"""
    try:
        init_bot_sync()
        
        json_data = request.get_json()
        update = Update.de_json(json_data, application.bot)
        
        # Обработаем обновление в отдельном потоке
        def process():
            loop.run_until_complete(application.process_update(update))
        
        thread = threading.Thread(target=process)
        thread.start()
        thread.join(timeout=30)  # Максимум 30 сек на обработку
        
        return "ok", 200
    
    except Exception as e:
        print(f"❌ Webhook ошибка: {e}")
        return "error", 500


@app.route("/health", methods=["GET"])
def health():
    return "🤖 Bot is running!", 200


@app.route("/", methods=["GET"])
def index():
    return "🇧🇷 Portuguese Tutor Bot is online!", 200


if __name__ == "__main__":
    if WEBHOOK_URL:
        print(f"🚀 Webhook режим активирован")
        print(f"   URL: {WEBHOOK_URL}/webhook")
        print(f"   Port: {PORT}")
    else:
        print(f"⚠️  WEBHOOK_URL не установлен (опционально)")
    
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
