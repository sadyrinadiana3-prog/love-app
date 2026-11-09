import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random
import json
import os
import datetime

BOT_TOKEN = "9237588674:AAEfZD8JL9GIn5yC04kyn9Y-DZYU5k41aIw"
# ВАЖНО: Сюда мы потом вставим ссылку от Render. Пока оставвстак
WEB_APP_URL = "https://love-app-rb47.onrender.com"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "webapp_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"meet_date": None, "plans": [], "custom_photo": None}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

LOVE_QUOTES = [
    "«Любовь — это не то, что ты находишь. Любовь — это то, что находит тебя.»",
    "«Мы выбираем, нас выбирают, Как это часто не совпадает!»",
    "«Одним взглядом можно убить любовь, одним же взглядом можно воскресить ее.» — Уильям Шекспир",
    "«Тоска по любви есть сама любовь.» — Жан Поль",
    "«Я люблю тебя не за то, кто ты, а за то, кто я, когда я с тобой.» — Маркес"
]

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=WEB_APP_URL)))
    await message.answer("Привет! Нажми на кнопку ниже, чтобы открыть наше общее окно.", reply_markup=builder.as_markup())

@dp.message(F.text == "/помощь")
async def help_cmd(message: types.Message):
    await message.answer("💖 Команды:\n/котик\n/любовь\n/цитата Текст\n/фото\n/дата 2026-12-31\n/дни\n/план Текст\n/отчет\n/удалить_план 1\n/очистить")

@dp.message(F.text == "/котик")
async def cat_cmd(message: types.Message):
    quote = random.choice(LOVE_QUOTES)
    await message.answer_photo(photo="https://i.ibb.co/gMq8VFT1/9d7b350f49f4d9d3f66ea7b9970013ed.jpg", caption=f"<blockquote>{quote}</blockquote>", parse_mode="HTML")

@dp.message(F.text == "/любовь")
async def love_cmd(message: types.Message):
    quote = random.choice(LOVE_QUOTES)
    await message.answer(f"<blockquote>{quote}</blockquote>", parse_mode="HTML")

@dp.message(F.text.startswith("/цитата "))
async def custom_quote(message: types.Message):
    text = message.text.replace("/цитата ", "")
    await message.answer(f"<blockquote>{text}</blockquote>", parse_mode="HTML")

@dp.message(F.text == "/фото")
async def photo_cmd(message: types.Message):
    await message.answer_photo(photo="https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg")

@dp.message(F.text == "/дни")
async def days_cmd(message: types.Message):
    data = load_data()
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        days = (meet - datetime.date.today()).days
        await message.answer(f"💖 До встречи осталось: {days} дн.!")
    else:
        await message.answer("❌ Дата не задана. Напиши /дата 2026-12-31")

@dp.message(F.text.startswith("/дата "))
async def set_date(message: types.Message):
    try:
        dt = message.text.replace("/дата ", "").strip()
        datetime.datetime.strptime(dt, "%Y-%m-%d")
        data = load_data()
        data["meet_date"] = dt
        save_data(data)
        await message.answer(f"✅ Дата установлена: {dt}")
    except:
        await message.answer("❌ Формат: /дата 2026-12-31")

@dp.message(F.text.startswith("/план "))
async def add_plan(message: types.Message):
    plan = message.text.replace("/план ", "").strip()
    if plan:
        data = load_data()
        data["plans"].append(plan)
        save_data(data)
        await message.answer(f"✅ План добавлен: {plan}")

@dp.message(F.text == "/отчет")
async def report(message: types.Message):
    data = load_data()
    text = "💖 **Отчет** 💖\n\n"
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        days = (meet - datetime.date.today()).days
        text += f"✈️ До встречи: {days} дн.\n"
    else:
        text += "✈️ Дата не задана\n"
    
    text += "\n📋 Планы:\n"
    if data["plans"]:
        for i, p in enumerate(data["plans"], 1):
            text += f"  {i}. {p}\n"
    else:
        text += "  Пусто\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.startswith("/удалить_план "))
async def delete_plan(message: types.Message):
    try:
        idx = int(message.text.replace("/удалить_план ", "").strip()) - 1
        data = load_data()
        if 0 <= idx < len(data["plans"]):
            removed = data["plans"].pop(idx)
            save_data(data)
            await message.answer(f"✅ Удален: {removed}")
        else:
            await message.answer("❌ Нет такого плана.")
    except:
        await message.answer("❌ Напиши номер: /удалить_план 1")

@dp.message(F.text == "/очистить")
async def clear_all(message: types.Message):
    save_data({"meet_date": None, "plans": [], "custom_photo": None})
    await message.answer("✅ Все данные удалены.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
