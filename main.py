from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, WebAppInfo, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
import os
import datetime
import random
import asyncio

app = FastAPI()
DATA_FILE = "webapp_data.json"

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

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"meet_date": None, "plans": [], "packing": [], "notes": [], "custom_photo": "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg"}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

# --- САЙТ (ОКНО) ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: sans-serif; background: #17212b; color: #fff; padding: 15px; text-align: center; }
        .card { background: #232e3c; border-radius: 15px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        img { width: 100%; border-radius: 10px; margin-bottom: 10px; max-height: 300px; object-fit: cover; }
        input, button { width: 100%; padding: 12px; margin: 5px 0; border-radius: 8px; border: none; font-size: 16px; box-sizing: border-box; }
        button { background: #2481cc; color: white; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:active { background: #1a5f99; transform: scale(0.98); }
        .date-big { font-size: 22px; margin: 15px 0; color: #64b5f6; font-weight: bold; }
        .item { text-align: left; padding: 8px; background: rgba(255,255,255,0.1); margin: 5px 0; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .del-btn { background: #e53935; width: auto; padding: 5px 10px; margin: 0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="card">
        <img id="mainPhoto" src="#">
        <h2>💖 Аниша и Диша 💖</h2>
        <div id="days" class="date-big">✈️ Загрузка...</div>
        <button onclick="showAlert()" style="background:#ff9800; margin-top:10px;">🔔 Показать уведомление</button>
    </div>
    
    <div class="card">
        <h3>🖼 Сменить фото</h3>
        <input type="text" id="photoInput" placeholder="Ссылка на новую картинку...">
        <button onclick="changePhoto()">Сохранить фото</button>
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

    <div class="card">
        <h3>🎒 Вещи в поездку</h3>
        <div id="packingList"></div>
        <input type="text" id="packingInput" placeholder="Что взять...">
        <button onclick="addPacking()">Добавить вещь</button>
    </div>

    <div class="card">
        <h3>📝 Заметки</h3>
        <div id="notesList"></div>
        <input type="text" id="noteInput" placeholder="Новая заметка...">
        <button onclick="addNote()">Добавить заметку</button>
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
            
            if (currentData.custom_photo) { document.getElementById('mainPhoto').src = currentData.custom_photo; }
            
            let renderList = (id, arr, key) => {
                let list = document.getElementById(id); list.innerHTML = '';
                arr.forEach((item, i) => {
                    let div = document.createElement('div'); div.className = 'item';
                    div.innerHTML = `<span>🔸 ${item}</span><button class="del-btn" onclick="delItem('${key}', ${i})">❌</button>`;
                    list.appendChild(div);
                });
            };
            renderList('plansList', currentData.plans, 'plans');
            renderList('packingList', currentData.packing, 'packing');
            renderList('notesList', currentData.notes, 'notes');
        }

        async function setDate() { let val = document.getElementById('dateInput').value; if (!val) return; currentData.meet_date = val; await saveData(); }
        async function changePhoto() { let val = document.getElementById('photoInput').value; if (!val) return; currentData.custom_photo = val; await saveData(); }
        async function addPlan() { let val = document.getElementById('planInput').value; if (!val) return; currentData.plans.push(val); document.getElementById('planInput').value = ''; await saveData(); }
        async function addPacking() { let val = document.getElementById('packingInput').value; if (!val) return; currentData.packing.push(val); document.getElementById('packingInput').value = ''; await saveData(); }
        async function addNote() { let val = document.getElementById('noteInput').value; if (!val) return; currentData.notes.push(val); document.getElementById('noteInput').value = ''; await saveData(); }
        async function delItem(key, index) { currentData[key].splice(index, 1); await saveData(); }

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

# --- БОТ (КОМАНДЫ) ---
@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=WEB_APP_URL)))
    await message.answer("Привет! Нажми на кнопку ниже, чтобы открыть наше общее окно. Или напиши /помощь.", reply_markup=builder.as_markup())

@dp.message(F.text == "/помощь")
async def help_cmd(message: types.Message):
    text = (
        "💖 **Все команды:**\n\n"
        "📸 /фото — отправить наше фото\n"
        "💌 /любовь — случайная цитата\n"
        "📅 /дата 2026-12-31 — дата встречи\n"
        "📊 /дни — уведомление\n"
        "📋 /план Текст — добавить план\n"
        "🎒 /вещь Текст — добавить вещь\n"
        "📝 /заметка Текст — добавить заметку\n"
        "📋 /отчет — полный список\n"
        "❌ /удалить_план 1 — удалить план\n"
        "❌ /удалить_вещь 1 — удалить вещь\n"
        "🗑 /очистить — удалить всё"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "/фото")
async def photo_cmd(message: types.Message):
    data = load_data()
    photo_url = data.get("custom_photo") or "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg"
    await message.answer_photo(photo=photo_url, caption="💖 Наша фоточка")

@dp.message(F.text == "/любовь")
async def love_cmd(message: types.Message):
    quote = random.choice(LOVE_QUOTES)
    await message.answer(f"<blockquote>{quote}</blockquote>", parse_mode="HTML")

@dp.message(F.text.startswith("/цитата "))
async def custom_quote(message: types.Message):
    text = message.text.replace("/цитата ", "")
    await message.answer(f"<blockquote>{text}</blockquote>", parse_mode="HTML")

@dp.message(F.text.startswith("/дата "))
async def set_date(message: types.Message):
    try:
        dt = message.text.replace("/дата ", "").strip()
        datetime.datetime.strptime(dt, "%Y-%m-%d")
        data = load_data(); data["meet_date"] = dt; save_data(data)
        await message.answer(f"✅ Дата установлена: {dt}")
    except: await message.answer("❌ Формат: /дата 2026-12-31")

@dp.message(F.text == "/дни")
async def days_cmd(message: types.Message):
    data = load_data()
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        days = (meet - datetime.date.today()).days
        await message.answer(f"💖 До встречи осталось: {days} дн.!")
    else: await message.answer("❌ Дата не задана.")

@dp.message(F.text.startswith("/план "))
async def add_plan(message: types.Message):
    plan = message.text.replace("/план ", "").strip()
    if plan:
        data = load_data(); data["plans"].append(plan); save_data(data)
        await message.answer(f"✅ План добавлен: {plan}")

@dp.message(F.text.startswith("/вещь "))
async def add_packing(message: types.Message):
    item = message.text.replace("/вещь ", "").strip()
    if item:
        data = load_data(); data["packing"].append(item); save_data(data)
        await message.answer(f"✅ Вещь добавлена: {item}")

@dp.message(F.text.startswith("/заметка "))
async def add_note(message: types.Message):
    note = message.text.replace("/заметка ", "").strip()
    if note:
        data = load_data(); data["notes"].append(note); save_data(data)
        await message.answer(f"✅ Заметка добавлена: {note}")

@dp.message(F.text == "/отчет")
async def report(message: types.Message):
    data = load_data()
    text = "💖 **Отчет** 💖\n\n"
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        text += f"✈️ До встречи: {(meet - datetime.date.today()).days} дн.\n"
    text += "\n📋 Планы:\n" + ("\n".join([f"  {i}. {p}" for i, p in enumerate(data["plans"], 1)]) if data["plans"] else "  Пусто")
    text += "\n\n🎒 Вещи:\n" + ("\n".join([f"  {i}. {p}" for i, p in enumerate(data["packing"], 1)]) if data["packing"] else "  Пусто")
    text += "\n\n📝 Заметки:\n" + ("\n".join([f"  {i}. {p}" for i, p in enumerate(data["notes"], 1)]) if data["notes"] else "  Пусто")
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text.startswith("/удалить_план "))
async def del_plan(message: types.Message):
    try:
        idx = int(message.text.replace("/удалить_план ", "").strip()) - 1
        data = load_data()
        if 0 <= idx < len(data["plans"]):
            removed = data["plans"].pop(idx); save_data(data)
            await message.answer(f"✅ Удален: {removed}")
    except: await message.answer("❌ Напиши номер: /удалить_план 1")

@dp.message(F.text.startswith("/удалить_вещь "))
async def del_packing(message: types.Message):
    try:
        idx = int(message.text.replace("/удалить_вещь ", "").strip()) - 1
        data = load_data()
        if 0 <= idx < len(data["packing"]):
            removed = data["packing"].pop(idx); save_data(data)
            await message.answer(f"✅ Удалена: {removed}")
    except: await message.answer("❌ Напиши номер: /удалить_вещь 1")

@dp.message(F.text == "/очистить")
async def clear_all(message: types.Message):
    data = load_data()
    data["meet_date"] = None; data["plans"] = []; data["packing"] = []; data["notes"] = []
    save_data(data)
    await message.answer("✅ Все данные удалены.")

# --- БОТ (INLINE РЕЖИМ) ---
@dp.inline_query()
async def inline_handler(query: types.InlineQuery):
    text = query.query.lower().strip()
    data = load_data()
    results = []

    commands = [
        ("/помощь", "📖 Список всех команд"),
        ("/любовь", "💌 Случайная цитата"),
        ("/отчет", "📊 Показать списки"),
        ("/дни", "📅 Сколько дней осталось"),
        ("/дата 2026-12-31", "📅 Установить дату"),
        ("/план Купить билеты", "📋 Добавить план"),
        ("/вещь Паспорт", "🎒 Добавить вещь"),
        ("/заметка Текст", "📝 Добавить заметку"),
    ]
    
    for cmd, desc in commands:
        if text in cmd.lower() or text in desc.lower() or not text:
            results.append(InlineQueryResultArticle(id=f"cmd_{cmd}", title=desc, description=f"Отправить: {cmd}", input_message_content=InputTextMessageContent(message_text=cmd)))

    if "план" in text or not text:
        for i, plan in enumerate(data["plans"]):
            results.append(InlineQueryResultArticle(id=f"plan_{i}", title=f"📋 {plan}", description="План", input_message_content=InputTextMessageContent(message_text=f"📋 Наш план: {plan}")))

    if "вещь" in text or not text:
        for i, item in enumerate(data["packing"]):
            results.append(InlineQueryResultArticle(id=f"pack_{i}", title=f"🎒 {item}", description="Вещь в поездку", input_message_content=InputTextMessageContent(message_text=f"🎒 Взять: {item}")))

    if "заметка" in text or not text:
        for i, note in enumerate(data["notes"]):
            results.append(InlineQueryResultArticle(id=f"note_{i}", title=f"📝 {note}", description="Заметка", input_message_content=InputTextMessageContent(message_text=f"📝 Заметка: {note}")))

    if "любовь" in text or not text:
        for i, quote in enumerate(LOVE_QUOTES):
            results.append(InlineQueryResultArticle(id=f"quote_{i}", title=f"💌 Цитата {i+1}", description=quote[:40]+"...", input_message_content=InputTextMessageContent(message_text=f"<blockquote>{quote}</blockquote>", parse_mode="HTML")))

    if "окно" in text or not text:
        results.append(InlineQueryResultArticle(
            id="open_app", title="💖 Открыть окно", description="Фото и планы",
            input_message_content=InputTextMessageContent(message_text="Нажми на кнопку ниже", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть", web_app=WebAppInfo(url=WEB_APP_URL))]]))
        ))

    await query.answer(results[:20], cache_time=1)

async def run_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_bot())
