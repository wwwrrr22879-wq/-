import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask
import threading

TOKEN = "7396521184:AAE6-GJkd7WCLnmImfI8urQh6FKStaYblK8"
ADMIN_CHAT_ID = -1003338724164
OWNER_ID = 7863316600

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_topic = {}
reply_map = {}
banned_users = set()

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💬 Общение")],
        [KeyboardButton(text="🆘 Поддержка")],
        [KeyboardButton(text="🤝 Общение и поддержка")]
    ],
    resize_keyboard=True
)

# ===== START =====
@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id in banned_users:
        return
    await message.answer("Выберите тему обращения 👇", reply_markup=menu)

# ===== ВЫБОР ТЕМЫ =====
@dp.message(F.text.in_(["💬 Общение", "🆘 Поддержка", "🤝 Общение и поддержка"]))
async def choose_topic(message: types.Message):
    user_topic[message.from_user.id] = message.text
    await message.answer("✉️ Напишите ваше сообщение")

# ===== СООБЩЕНИЯ =====
@dp.message()
async def messages(message: types.Message):
    uid = message.from_user.id

    if uid in banned_users:
        return

    # ===== ПОЛЬЗОВАТЕЛЬ → АДМИНЫ =====
    if message.chat.id != ADMIN_CHAT_ID:
        topic = user_topic.get(uid, "Без темы")
        username = f"@{message.from_user.username}" if message.from_user.username else "Без юзернейма"

        text = (
            "Сообщение от пользователя💌\n"
            f"Тема: {topic}\n"
            f"Юзер: {username}\n"
            f"ID: {uid}\n\n"
            f"{message.text}"
        )

        sent = await bot.send_message(ADMIN_CHAT_ID, text)
        reply_map[sent.message_id] = uid

    # ===== АДМИН → ПОЛЬЗОВАТЕЛЮ =====
    else:
        if not message.reply_to_message:
            return

        user_id = reply_map.get(message.reply_to_message.message_id)
        if not user_id:
            return

        # ===== БАН / РАЗБАН =====
        if message.from_user.id == OWNER_ID and message.text:
            if message.text.startswith("/ban"):
                banned_users.add(user_id)
                await bot.send_message(ADMIN_CHAT_ID, f"⛔ Пользователь {user_id} забанен")
                return
            if message.text.startswith("/unban"):
                banned_users.discard(user_id)
                await bot.send_message(ADMIN_CHAT_ID, f"✅ Пользователь {user_id} разбанен")
                return

        try:
            await bot.send_message(
                user_id,
                "Ответ администратора💌\n\n" + message.text
            )
        except:
            pass

# ===== СПИСОК БАНОВ =====
@dp.message(Command("banlist"))
async def banlist(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
    if not banned_users:
        await message.answer("Список банов пуст")
    else:
        await message.answer("🚫 Забаненные:\n" + "\n".join(map(str, banned_users)))

# ===== KEEP ALIVE =====
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run():
    app.run("0.0.0.0", 8080)

threading.Thread(target=run).start()

# ===== RUN =====
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
