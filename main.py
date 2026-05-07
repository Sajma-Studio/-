import asyncio
import re
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ChatPermissions, ReplyKeyboardMarkup, KeyboardButton
from database import Database

# --- КОНФІГУРАЦІЯ ---
TOKEN = "ТВІЙ_ТОКЕН"
MY_ID = 7518373450 

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database("power.db")

user_last_msg = {}
MAT_WORDS = ["хуй", "пздц", "єблан", "бля", "сука"] # Твої 100+ слів

async def is_admin(chat_id, user_id):
    if user_id == MY_ID: return True
    m = await bot.get_chat_member(chat_id, user_id)
    return m.status in ["administrator", "creator"]

# --- МОДЕРУВАННЯ (БАН, МУТ, ПОП) ---
@dp.message(lambda m: any(m.text.lower().startswith(x) for x in ["бан", "забанити", "мут", "замутити", "поп", "попередження"]))
async def mod_action(message: types.Message):
    if not await is_admin(message.chat.id, message.from_user.id): return
    if not message.reply_to_message: return await message.reply("⚠️ Відповідай на повідомлення!")

    target = message.reply_to_message.from_user
    text = message.text.lower()

    if text.startswith("бан") or text.startswith("забанити"):
        await bot.ban_chat_member(message.chat.id, target.id)
        await message.answer(f"🚫 <b>{target.full_name}</b> забанений!")
    elif text.startswith("мут") or text.startswith("замутити"):
        await bot.restrict_chat_member(message.chat.id, target.id, permissions=ChatPermissions(can_send_messages=False), until_date=int(time.time())+3600)
        await message.answer(f"🔇 <b>{target.full_name}</b> в муті на годину.")
    elif text.startswith("поп") or text.startswith("попередження"):
        w = db.add_warn(target.id)
        if w >= 3:
            await bot.ban_chat_member(message.chat.id, target.id)
            db.reset_warns(target.id)
            await message.answer(f"🚫 {target.full_name} отримав 3/3 варнів і забанений!")
        else:
            await message.answer(f"⚠️ {target.full_name} отримав попередження ({w}/3)")

# --- ГЛОБАЛЬНИЙ МОНІТОРИНГ ---
@dp.message()
async def global_monitor(message: types.Message):
    if not message.text or message.chat.type == "private": return
    uid = message.from_user.id
    cid = message.chat.id

    # Оновлення статистики
    db.update_stats(uid, message.from_user.full_name)

    # Якщо пише АДМІН — фільтри не діють
    admin_status = await is_admin(cid, uid)

    if not admin_status:
        # 1. Анти-Посилання (URL, t.me, @username)
        if db.get_setting(cid, "anti_link"):
            link_pattern = r"(http://|https://|t\.me/|@\w+)"
            if re.search(link_pattern, message.text.lower()):
                await message.delete()
                return await message.answer(f"🚫 {message.from_user.first_name}, посилання заборонені!")

        # 2. Анти-Рос
        if db.get_setting(cid, "anti_rus") and re.search(r'[ыэъёЫЭЪЁ]', message.text):
            return await message.delete()

        # 3. Анти-Мат
        if db.get_setting(cid, "anti_mat") and any(w in message.text.lower() for w in MAT_WORDS):
            return await message.delete()

    # Спеціальні команди власника
    if uid == MY_ID:
        if "адміни сюди" in message.text.lower():
            admins = await bot.get_chat_administrators(cid)
            tags = " ".join([a.user.mention_html() for a in admins if not a.user.is_bot])
            await message.answer(f"📢 Власник кличе адмінів!\n{tags}", parse_mode="HTML")
        
        # Налаштування через текст
        if message.text == "Топл Анти-Посилання":
            cur = db.get_setting(cid, "anti_link")
            db.set_setting(cid, "anti_link", 1 if not cur else 0)
            await message.answer(f"🔄 Анти-Посилання тепер {'Увімкнено ✅' if not cur else 'Вимкнено ❌'}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
