import asyncio
import sqlite3
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- КОНФІГУРАЦІЯ ---
TOKEN = "8694438105:AAE66_9D1ZYLfwMn5AEEKWc3bPyYeUF5zTU"
MY_ID = 7518373450 

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАНИХ (Фільтри + Статистика) ---
def init_db():
    conn = sqlite3.connect("power_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_settings (
            chat_id BIGINT PRIMARY KEY,
            anti_rus INTEGER DEFAULT 0,
            anti_mat INTEGER DEFAULT 0,
            anti_flood INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            warns INTEGER DEFAULT 0,
            last_msg_time REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def get_setting(chat_id, setting):
    conn = sqlite3.connect("power_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT {setting} FROM chat_settings WHERE chat_id = ?", (chat_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0

def toggle_setting(chat_id, setting, value):
    conn = sqlite3.connect("power_bot.db")
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO chat_settings (chat_id, {setting}) VALUES (?, ?) ON CONFLICT(chat_id) DO UPDATE SET {setting} = ?", (chat_id, value, value))
    conn.commit()
    conn.close()

# --- ПЕРЕВІРКА ТЕКСТУ ---

BAD_WORDS = ["мат1", "мат2", "хуй", "пздц"] # Сюди додай список матів

def has_russian_letters(text):
    # Шукаємо символи: ы, э, ъ, ё
    return bool(re.search(r'[ыэъёЫЭЪЁ]', text))

def has_bad_words(text):
    for word in BAD_WORDS:
        if word in text.lower():
            return True
    return False

# --- ОБРОБНИКИ НАЛАШТУВАНЬ ---

@dp.message(Command("settings"))
async def show_settings(message: types.Message):
    # Лише адмін може бачити налаштування
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"] and message.from_user.id != MY_ID:
        return

    rus = "✅" if get_setting(message.chat.id, "anti_rus") else "❌"
    mat = "✅" if get_setting(message.chat.id, "anti_mat") else "❌"
    flood = "✅" if get_setting(message.chat.id, "anti_flood") else "❌"

    text = (
        f"🛠 **Налаштування фільтрів чату**\n\n"
        f"1️⃣ Анти-Рос (ы, э, ъ, ё): {rus}\n"
        f"2️⃣ Анти-Мат: {mat}\n"
        f"3️⃣ Анти-Флуд: {flood}\n\n"
        f"Використовуйте кнопки для перемикання:"
    )
    
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Увімкнути/Вимкнути Анти-Рос")],
        [KeyboardButton(text="Увімкнути/Вимкнути Анти-Мат")],
        [KeyboardButton(text="Назад")]
    ], resize_keyboard=True)
    
    await message.answer(text, reply_markup=kb)

# Логіка перемикання (спрощено)
@dp.message(F.text.contains("Анти-Рос"))
async def toggle_rus(message: types.Message):
    current = get_setting(message.chat.id, "anti_rus")
    toggle_setting(message.chat.id, "anti_rus", 1 if not current else 0)
    await message.answer("Змінено! Перевірте /settings")

# --- ГОЛОВНИЙ МОНІТОРИНГ ---

@dp.message()
async def monitor_everything(message: types.Message):
    if not message.text or message.chat.type == "private": return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # 1. Перевірка на російські літери
    if get_setting(chat_id, "anti_rus") and has_russian_letters(message.text):
        await message.delete()
        await message.answer(f"⚠️ {message.from_user.mention_html()}, у нас заборонено використовувати російські літери (ы, э, ъ, ё)!", parse_mode="HTML")
        return

    # 2. Перевірка на мат
    if get_setting(chat_id, "anti_mat") and has_bad_words(message.text):
        await message.delete()
        # Тут можна викликати функцію додавання варна (поп)
        await message.answer(f"⚠️ {message.from_user.mention_html()}, не матірся! Отримано попередження.", parse_mode="HTML")
        return

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
