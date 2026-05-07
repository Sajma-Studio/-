import asyncio
import re
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ChatPermissions, ReplyKeyboardMarkup, KeyboardButton
from database import Database

# --- КОНФІГУРАЦІЯ ---
TOKEN = "8694438105:AAE66_9D1ZYLfwMn5AEEKWc3bPyYeUF5zTU"
MY_ID = 7518373450 

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database("power.db")

# Словник для анти-спаму (час останнього повідомлення)
user_last_msg = {}

# Список матерних слів (додай свої 100+)
MAT_WORDS = ["хуй", "пздц", "єблан", "бля", "сука"] 

# --- ДОПОМІЖНІ ФУНКЦІЇ ---

async def is_admin(chat_id, user_id):
    if user_id == MY_ID: return True
    m = await bot.get_chat_member(chat_id, user_id)
    return m.status in ["administrator", "creator"]

# --- ОБРОБНИК СТІКЕРІВ (АНТИ-РОС ПАКИ) ---

@dp.message(F.sticker)
async def check_sticker(message: types.Message):
    if not db.get_setting(message.chat.id, "anti_rus"): return
    
    pack_name = message.sticker.set_name
    if pack_name and re.search(r'[ыэъёЫЭЪЁ]', pack_name):
        try:
            await message.delete()
            w = db.add_warn(message.from_user.id)
            await message.answer(f"⚠️ {message.from_user.mention_html()}, варн за рос. стікерпак! ({w}/3)", parse_mode="HTML")
            if w >= 3:
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                db.reset_warns(message.from_user.id)
        except: pass

# --- КОМАНДИ МОДЕРАЦІЇ (ПОВНІ ТА СКОРОЧЕНІ) ---

@dp.message(lambda m: any(m.text.lower().startswith(x) for x in ["бан", "забанити", "мут", "замутити", "поп", "попередження"]))
async def mod_action(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message:
        return await message.reply("⚠️ Потрібна відповідь на повідомлення!")

    target = message.reply_to_message.from_user
    text = message.text.lower()

    # БАН (Дозволено власнику банити адмінів)
    if text.startswith("бан") or text.startswith("забанити"):
        try:
            await bot.ban_chat_member(message.chat.id, target.id)
            await message.answer(f"🚫 <b>{target.full_name}</b> вилетів з чату!", parse_mode="HTML")
        except:
            await message.reply("❌ Не вдалося забанити. Перевірте мої права.")

    # МУТ
    elif text.startswith("мут") or text.startswith("замутити"):
        until = int(time.time()) + 3600
        await bot.restrict_chat_member(message.chat.id, target.id, 
            permissions=ChatPermissions(can_send_messages=False), until_date=until)
        await message.answer(f"🔇 <b>{target.full_name}</b> замучений на годину.", parse_mode="HTML")

    # ВАРН
    elif text.startswith("поп") or text.startswith("попередження"):
        w = db.add_warn(target.id)
        if w >= 3:
            await bot.ban_chat_member(message.chat.id, target.id)
            db.reset_warns(target.id)
            await message.answer(f"🚫 {target.mention_html()} отримав 3/3 і забанений!", parse_mode="HTML")
        else:
            await message.answer(f"⚠️ {target.mention_html()} отримав попередження ({w}/3)", parse_mode="HTML")

# --- СТАТИСТИКА ТА ТОП ---

@dp.message(lambda m: m.text.lower() in ["стат", "статистика", "топ"])
async def stats_engine(message: types.Message):
    if message.text.lower() in ["стат", "статистика"]:
        res = db.get_user(message.from_user.id)
        if res:
            await message.reply(f"📊 <b>Статистика {message.from_user.first_name}:</b>\n✉️ Повідомлень: {res[0]}\n⚠️ Варнів: {res[1]}/3", parse_mode="HTML")
    
    elif message.text.lower() == "топ":
        # Це вимагає методу get_top_messages у вашому класі Database
        # Спрощений приклад:
        await message.answer("🏆 Функція ТОП активується через базу даних...")

# --- МОНІТОРИНГ ТЕКСТУ ТА ТЕГИ ---

@dp.message()
async def global_monitor(message: types.Message):
    if not message.text or message.chat.type == "private": return
    
    uid = message.from_user.id
    chat_id = message.chat.id

    # 1. Анти-спам (1 сек)
    now = time.time()
    if uid in user_last_msg and now - user_last_msg[uid] < 0.8:
        return await message.delete()
    user_last_msg[uid] = now

    # 2. Оновлення БД
    db.update_stats(uid, message.from_user.full_name)

    # 3. Анти-Рос та Анти-Мат
    if db.get_setting(chat_id, "anti_rus") and re.search(r'[ыэъёЫЭЪЁ]', message.text):
        return await message.delete()
    
    if db.get_setting(chat_id, "anti_mat") and any(w in message.text.lower() for w in MAT_WORDS):
        return await message.delete()

    # 4. Система тегів від власника (Коли ти пишеш кодові слова)
    if uid == MY_ID:
        if "адміни сюди" in message.text.lower():
            admins = await bot.get_chat_administrators(chat_id)
            tags = " ".join([a.user.mention_html() for a in admins if not a.user.is_bot])
            await message.answer(f"📢 <b>Власник кличе адмінів!</b>\n{tags}", parse_mode="HTML")
        
        elif "всім увага" in message.text.lower():
            await message.answer("📢 <b>УВАГА ВСІМ УЧАСНИКАМ! Читайте повідомлення власника!</b>", parse_mode="HTML")

    # 5. Кнопки налаштувань (якщо адмін написав /settings)
    if message.text == "Топл Анти-Рос" and await is_admin(chat_id, uid):
        cur = db.get_setting(chat_id, "anti_rus")
        db.set_setting(chat_id, "anti_rus", 1 if not cur else 0)
        await message.answer("🔄 Фільтр Анти-Рос змінено!")

async def main():
    print("Містер Потужність запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
