from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession
import json
import os
import asyncio
import datetime
import random

app = FastAPI()
DATA_FILE = "webapp_data.json"

# --- НАСТРОЙКИ БОТА ---
BOT_TOKEN = "9237588674:AAEfZD8JL9GIn5yC04kyn9Y-DZYU5k41aIw"
WEB_APP_URL = "https://love-app-rb47.onrender.com"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

LOVE_QUOTES = [
    "«Любовь — это не то, что ты находишь. Любовь — это то, что находит тебя.»",
    "«Мы выбираем, нас выбирают, Как это часто не совпадает!»",
    "«Одним взглядом можно убить любовь, одним же взглядом можно воскресить ее.» — Уильям Шекспир",
    "«Тоска по любви есть сама любовь.» — Жан Поль",
    "«Я люблю тебя не за то, кто ты, а за то, кто я, когда я с тобой.» — Маркес"
]

# --- ФУНКЦИИ ДЛЯ САЙТА ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"meet_date": None, "plans": [], "custom_photo": None}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: sans-serif; background: #17212b; color: #fff; padding: 15px; text-align: center; }
        .card { background: #232e3c; border-radius: 15px; padding: 15px; margin-bottom: 15px; }
        img { width: 100%; border-radius: 10px; margin-bottom: 10px; max-height: 300px; object-fit: cover; }
        input, button { width: 100%; padding: 12px; margin: 5px 0; border-radius: 8px; border: none; font-size: 16px; box-sizing: border-box; }
        button { background: #2481cc; color: white; font-weight: bold; cursor: pointer; }
        .date-big { font-size: 22px; margin: 15px 0; color: #64b5f6; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <img id="mainPhoto" src="https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg">
        <h2>💖 Аниша и Диша 💖</h2>
        <div id="days" class="date-big">✈️ Загрузка...</div>
        <button onclick="showAlert()" style="background:#ff9800; margin-top:10px;">🔔 Показать уведомление</button>
    </div>
    <div class="card">
        <h3>📅 Дата встречи</h3>
        <input type="date" id="dateInput">
        <button onclick="setDate()">Сохранить дату</button>
    </div>
    <div class="card">
        <h3>📋 Планы</h3>
        <div id="plansList"></div>
        <input type="text" id="planInput" placeholder="Новый план...">
        <button onclick="addPlan()">Добавить план</button>
    </div>
    <script>
        let tg = window.Telegram.WebApp; tg.expand();
        let currentData = {};
        function showAlert() {
            if (currentData.meet_date) {
                let meet = new Date(currentData.meet_date); let today = new Date();
                let diff = Math.ceil((meet - today) / (1000 * 60 * 60 * 24));
                tg.showAlert(`💖 До встречи осталось: ${diff} дн.!`);
            } else { tg.showAlert("💖 Дата встречи не задана"); }
        }
        async function loadData() {
            let res = await fetch('/api/data'); currentData = await res.json(); updateUI();
        }
        function updateUI() {
            if (currentData.meet_date) {
                let meet = new Date(currentData.meet_date); let today = new Date();
                let diff = Math.ceil((meet - today) / (1000 * 60 * 60 * 24));
                document.getElementById('days').innerText = `✈️ До встречи: ${diff} дн.`;
                document.getElementById('dateInput').value = currentData.meet_date;
            } else { document.getElementById('days').innerText = "✈️ Дата не задана"; }
            let list = document.getElementById('plansList'); list.innerHTML = '';
            currentData.plans.forEach((p, index) => {
                let div = document.createElement('div'); div.style.textAlign = "left"; div.style.padding = "5px"; div.innerHTML = "🔸 " + p;
                list.appendChild(div);
            });
        }
        async function setDate() {
            let val = document.getElementById('dateInput').value; if (!val) return;
            currentData.meet_date = val; await saveData();
        }
        async function addPlan() {
            let val = document.getElementById('planInput').value; if (!val) return;
            currentData.plans.push(val); document.getElementById('planInput').value = ''; await saveData();
        }
        async function saveData() {
            await fetch('/api/data', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(currentData) });
            updateUI();
        }
        loadData();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE

@app.get("/api/data")
async def get_data():
    return load_data()

@app.post("/api/data")
async def update_data(data: dict):
    save_data(data)
    return {"status": "ok"}

# --- КОМАНДЫ БОТА ---
@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=WEB_APP_URL)))
    await message.answer("Привет! Нажми на кнопку ниже, чтобы открыть наше общее окно.", reply_markup=builder.as_markup())

@dp.message(F.text == "/любовь")
async def love_cmd(message: types.Message):
    quote = random.choice(LOVE_QUOTES)
    await message.answer(f"<blockquote>{quote}</blockquote>", parse_mode="HTML")

@dp.message(F.text.startswith("/дата "))
async def set_date(message: types.Message):
    try:
        dt = message.text.replace("/дата ", "").strip()
        datetime.datetime.strptime(dt, "%Y-%m-%d")
        data = load_data(); data["meet_date"] = dt; save_data(data)
        await message.answer(f"✅ Дата установлена: {dt}")
    except: await message.answer("❌ Формат: /дата 2026-12-31")

@dp.message(F.text.startswith("/план "))
async def add_plan(message: types.Message):
    plan = message.text.replace("/план ", "").strip()
    if plan:
        data = load_data(); data["plans"].append(plan); save_data(data)
        await message.answer(f"✅ План добавлен: {plan}")

@dp.message(F.text == "/отчет")
async def report(message: types.Message):
    data = load_data()
    text = "💖 **Отчет** 💖\n\n"
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        text += f"✈️ До встречи: {(meet - datetime.date.today()).days} дн.\n"
    text += "\n📋 Планы:\n" + ("\n".join([f"  {i}. {p}" for i, p in enumerate(data["plans"], 1)]) if data["plans"] else "  Пусто")
    await message.answer(text, parse_mode="Markdown")

# --- ЗАПУСК БОТА В ФОНЕ ---
async def run_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())
