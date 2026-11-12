
import os 
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (InlineKeyboardButton, WebAppInfo, InlineQueryResultArticle, 
                           InlineQueryResultPhoto, InputTextMessageContent)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import datetime
import random
import asyncio
import uuid

# Импорт нашей базы данных
from database import init_db, async_session, Couple
from sqlalchemy import select

app = FastAPI()

BOT_TOKEN = "BOT_TOKEN = os.getenv("BOT_TOKEN")"
SERVER_URL = "https://love-app-rb47.onrender.com"
MINI_APP_URL = "https://t.me/anisha_disha_2026_bot/love_window"
MUSIC_URL = "https://example.com/love.mp3"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

LOVE_QUOTES = [
    "«Любовь — это не то, что ты находишь. Любовь — это то, что находит тебя.»",
    "«Мы выбираем, нас выбирают, Как это часто не совпадает!»",
    "«Одним взглядом можно убить любовь, одним же взглядом можно воскресить ее.» — <i>Уильям Шекспир</i>",
    "«Тоска по любви есть сама любовь.» — <i>Жан Поль</i>",
    "«Я люблю тебя не за то, кто ты, а за то, кто я, когда я с тобой.» — <i>Маркес</i>"
]

# --- РАБОТА С БАЗОЙ ---
async def get_user_couple(user_id: int, create_if_missing=True):
    async with async_session() as session:
        result = await session.execute(select(Couple).where((Couple.user1_id == user_id) | (Couple.user2_id == user_id)))
        couple = result.scalar_one_or_none()
        
        if not couple and create_if_missing:
            new_code = f"LOVE-{uuid.uuid4().hex[:4].upper()}"
            couple = Couple(user1_id=user_id, invite_code=new_code, data_json={
                "meet_date": None, "plans": [], "packing": [], "notes": [], 
                "custom_photo": "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg", 
                "title": "💖 Дина и Аниша 💖", # <-- Изменено начальное название
                "bg_color": "#17212b", "btn_color": "#2481cc", 
                "rel_date": None, "font_size": "22px", "font_style": "italic"
            })
            session.add(couple)
            await session.commit()
            await session.refresh(couple)
        return couple

async def update_couple_data(couple_id: int, data: dict):
    async with async_session() as session:
        result = await session.execute(select(Couple).where(Couple.id == couple_id))
        couple = result.scalar_one_or_none()
        if couple:
            couple.data_json = data
            await session.commit()

# --- САЙТ (ОКНО) ---
HTML_PAGE = """ 
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root { --bg: #17212b; --card-bg: #232e3c; --btn: #2481cc; --text: #fff; --font-size: 22px; --font-style: italic; }
        body { font-family: 'Helvetica Neue', Arial, sans-serif; background: var(--bg); color: var(--text); padding: 15px; text-align: center; transition: 0.3s; }
        .card { background: var(--card-bg); border-radius: 15px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        img { width: 100%; border-radius: 10px; margin-bottom: 10px; max-height: 300px; object-fit: cover; }
        input, button { width: 100%; padding: 12px; margin: 5px 0; border-radius: 8px; border: none; font-size: 16px; box-sizing: border-box; }
        button { background: var(--btn); color: white; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:active { opacity: 0.8; transform: scale(0.98); }
        .date-big { font-size: var(--font-size); margin: 15px 0; color: #64b5f6; font-weight: bold; font-style: var(--font-style); }
        .item { text-align: left; padding: 8px; background: rgba(255,255,255,0.1); margin: 5px 0; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .item.done { opacity: 0.5; text-decoration: line-through; }
        .del-btn { background: #e53935; width: auto; padding: 5px 10px; margin: 0 0 0 5px; font-size: 14px; }
        .done-btn { background: #43a047; width: auto; padding: 5px 10px; margin: 0; font-size: 14px; }
        h2 { font-style: italic; text-shadow: 0 0 10px rgba(255,255,255,0.2); }
        .stat-box { font-size: 18px; margin: 10px 0; }
        .bottom-settings { border-top: 2px solid var(--btn); padding-top: 15px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <img id="mainPhoto" src="#">
        <h2 id="appTitle"></h2>
        <div id="days" class="date-big">✈️ Загрузка...</div>
        <div id="relStats" class="stat-box"></div>
        <button onclick="showAlert()" style="background:#ff9800; margin-top:10px;">🔔 Показать уведомление</button>
    </div>
    <div class="card">
        <h3>📅 Даты</h3>
        <input type="date" id="dateInput">
        <button onclick="setDate()">Дата встречи</button>
        <input type="date" id="relDateInput">
        <button onclick="setRelDate()">Дата отношений</button>
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
    <div class="card bottom-settings">
        <h3>🎨 Стиль и Настройки</h3>
        <!-- ДОБАВЛЕНО ПОЛЕ ДЛЯ НАЗВАНИЯ -->
        <p><b>Название окна:</b></p>
        <input type="text" id="titleInput" placeholder="Например: Дина и Аниша">
        <button onclick="updateTitle()" style="background:#ff9800;">Изменить название</button>
        
        <p><b>Цвета:</b></p>
        <input type="text" id="bgColor" placeholder="Цвет фона (например, #17212b)">
        <input type="text" id="btnColor" placeholder="Цвет кнопок (например, #2481cc)">
        <p><b>Текст:</b></p>
        <input type="text" id="fontSize" placeholder="Размер (например, 22px)">
        <select id="fontStyle" style="width:100%; padding:12px; margin:5px 0; border-radius:8px; border:none; font-size:16px;">
            <option value="normal">Обычный</option>
            <option value="italic">Курсив</option>
            <option value="bold">Жирный</option>
        </select>
        <p><b>Фото:</b></p>
        <input type="text" id="photoInput" placeholder="Ссылка на новую картинку...">
        <button onclick="applyAllSettings()" style="background:#4caf50;">Применить всё</button>
    </div>
    <script>
        let tg = window.Telegram.WebApp; tg.expand();
        let currentData = {};
        let alertShown = false;
        let userId = tg.initDataUnsafe?.user?.id || 0;

        function showAlert() {
            if (currentData.meet_date) {
                let meet = new Date(currentData.meet_date); let today = new Date();
                let diff = Math.ceil((meet - today) / (1000 * 60 * 60 * 24));
                tg.showAlert(`💖 До встречи осталось: ${diff} дн.!`);
            } else { tg.showAlert("💖 Дата встречи не задана"); }
        }

        async function loadData() {
            let res = await fetch(`/api/data?user_id=${userId}`); 
            currentData = await res.json(); updateUI();
            if (!alertShown && currentData.meet_date) {
                alertShown = true;
                let meet = new Date(currentData.meet_date); let today = new Date();
                let diff = Math.ceil((meet - today) / (1000 * 60 * 60 * 24));
                setTimeout(() => {
                    tg.showPopup({ title: "💖 Наше окно", message: `До встречи осталось: ${diff} дн.!`, buttons: [{type: "ok"}] });
                }, 500);
            }
        }

        function updateUI() {
            if (currentData.title) { 
                document.getElementById('appTitle').innerText = currentData.title; 
                document.getElementById('titleInput').value = currentData.title; // Заполняем поле названия
            }
            if (currentData.bg_color) document.documentElement.style.setProperty('--bg', currentData.bg_color);
            if (currentData.btn_color) document.documentElement.style.setProperty('--btn', currentData.btn_color);
            if (currentData.font_size) document.documentElement.style.setProperty('--font-size', currentData.font_size);
            if (currentData.font_style) document.documentElement.style.setProperty('--font-style', currentData.font_style);
            if (currentData.meet_date) {
                let meet = new Date(currentData.meet_date); let today = new Date();
                let diff = Math.ceil((meet - today) / (1000 * 60 * 60 * 24));
                document.getElementById('days').innerText = `✈️ До встречи: ${diff} дн.`;
                document.getElementById('dateInput').value = currentData.meet_date;
            } else { document.getElementById('days').innerText = "✈️ Дата не задана"; }
            if (currentData.rel_date) {
                let rel = new Date(currentData.rel_date); let today = new Date();
                let diff = Math.floor((today - rel) / (1000 * 60 * 60 * 24));
                document.getElementById('relStats').innerText = `❤️ Вместе уже: ${diff} дн.`;
                document.getElementById('relDateInput').value = currentData.rel_date;
            }
            if (currentData.custom_photo) { document.getElementById('mainPhoto').src = currentData.custom_photo; }
            let renderList = (id, arr, key) => {
                let list = document.getElementById(id); list.innerHTML = '';
                arr.forEach((item, i) => {
                    let div = document.createElement('div'); 
                    div.className = 'item' + (item.done ? ' done' : '');
                    div.innerHTML = `
                        <span>${item.done ? '✅' : '🔸'} ${item.text}</span>
                        <div>
                            <button class="done-btn" onclick="toggleItem('${key}', ${i})">${item.done ? '↩️' : '✔️'}</button>
                            <button class="del-btn" onclick="delItem('${key}', ${i})">❌</button>
                        </div>
                    `;
                    list.appendChild(div);
                });
            };
            let formatArr = (arr) => arr.map(item => typeof item === 'string' ? {text: item, done: false} : item);
            renderList('plansList', formatArr(currentData.plans), 'plans');
            renderList('packingList', formatArr(currentData.packing), 'packing');
            renderList('notesList', formatArr(currentData.notes), 'notes');
        }

        // НОВАЯ ФУНКЦИЯ ДЛЯ ИЗМЕНЕНИЯ НАЗВАНИЯ
        async function updateTitle() {
            let newTitle = document.getElementById('titleInput').value;
            if (newTitle.trim()) {
                currentData.title = newTitle;
                await saveData();
                tg.showAlert("✅ Название успешно изменено!");
            } else {
                tg.showAlert("❌ Название не может быть пустым.");
            }
        }

        async function setDate() { let val = document.getElementById('dateInput').value; if (!val) return; currentData.meet_date = val; await saveData(); }
        async function setRelDate() { let val = document.getElementById('relDateInput').value; if (!val) return; currentData.rel_date = val; await saveData(); }
        async function applyAllSettings() { 
            if (document.getElementById('bgColor').value) currentData.bg_color = document.getElementById('bgColor').value;
            if (document.getElementById('btnColor').value) currentData.btn_color = document.getElementById('btnColor').value;
            if (document.getElementById('fontSize').value) currentData.font_size = document.getElementById('fontSize').value;
            currentData.font_style = document.getElementById('fontStyle').value;
            if (document.getElementById('photoInput').value) currentData.custom_photo = document.getElementById('photoInput').value;
            await saveData(); 
        }
        async function addPlan() { let val = document.getElementById('planInput').value; if (!val) return; currentData.plans.push({text: val, done: false}); document.getElementById('planInput').value = ''; await saveData(); }
        async function addPacking() { let val = document.getElementById('packingInput').value; if (!val) return; currentData.packing.push({text: val, done: false}); document.getElementById('packingInput').value = ''; await saveData(); }
        async function addNote() { let val = document.getElementById('noteInput').value; if (!val) return; currentData.notes.push({text: val, done: false}); document.getElementById('noteInput').value = ''; await saveData(); }
        async function toggleItem(key, index) { currentData[key][index].done = !currentData[key][index].done; await saveData(); }
        async function delItem(key, index) { currentData[key].splice(index, 1); await saveData(); }

        async function saveData() {
            await fetch(`/api/data?user_id=${userId}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(currentData) });
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
async def get_data(user_id: int):
    couple = await get_user_couple(user_id)
    return couple.data_json

@app.post("/api/data")
async def update_data(data: dict, user_id: int):
    couple = await get_user_couple(user_id)
    await update_couple_data(couple.id, data)
    return {"status": "ok"}

# --- БОТ (КОМАНДЫ) ---
@dp.message(CommandStart(deep_link=True))
async def start_with_code(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    code = command.args 
    async with async_session() as session:
        result = await session.execute(select(Couple).where(Couple.invite_code == code))
        couple = result.scalar_one_or_none()
        if couple and couple.user2_id is None and couple.user1_id != user_id:
            couple.user2_id = user_id
            await session.commit()
            await message.answer("🎉 Вы успешно связаны! Теперь ваши планы и заметки будут общими. Открывайте окно!")
        elif couple and couple.user1_id == user_id:
            await message.answer("Это ваш собственный код приглашения. Отправьте его партнеру.")
        else:
            await message.answer("❌ Код не найден или уже использован. Попросите партнера создать новый.")
            await get_user_couple(user_id) 

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=SERVER_URL)))
    await message.answer("Нажми на кнопку ниже, чтобы открыть общее окно.", reply_markup=builder.as_markup())

@dp.message(CommandStart())
async def start(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=SERVER_URL)))
    await message.answer(f"Привет! Твой код приглашения для партнера:\n<code>{couple.invite_code}</code>\n\nСкинь его партнеру или отправь ссылку:\nhttps://t.me/{(await bot.get_me()).username}?start={couple.invite_code}\n\nЕсли не знаешь, что делать, напиши /гайд", reply_markup=builder.as_markup(), parse_mode="HTML")

# --- НОВАЯ КОМАНДА ГАЙД ---
@dp.message(F.text == "/гайд")
async def guide(message: types.Message):
    text = (
        "📖 <b>Подробный гайд по боту Love App</b>\n\n"
        "Этот бот создан для пар, которые хотят вести общие планы, списки вещей и заметки, даже находясь на расстоянии.\n\n"
        
        "👫 <b>1. Как пригласить партнера?</b>\n"
        "• Напиши команду /мой_код (или посмотри код в приветствии).\n"
        "• Скопируй ссылку, которую пришлет бот, и отправь её своему партнеру.\n"
        "• Как только партнер перейдет по ссылке и нажмет «Start», вы будете связаны! Теперь вы видите одни и те же данные.\n\n"
        
        "💻 <b>2. Как открыть Mini App (Окно)?</b>\n"
        "• Нажми на кнопку <b>«💖 Открыть наше окно»</b> под любым сообщением бота.\n"
        "• Внутри окна ты можешь добавлять планы, вещи в поездку и заметки. Все изменения мгновенно сохраняются и видны партнеру.\n"
        "• Внизу окна есть настройки: можно поменять цвета, шрифт, картинку и <b>название окна</b> (например, написать имена)!\n\n"
        
        "🛠 <b>3. Основные команды бота:</b>\n"
        "📅 /дата 2026-12-31 — установить дату встречи (бот будет считать дни).\n"
        "❤️ /отношения 2024-01-01 — установить дату начала отношений.\n"
        "📊 /дни — узнать, сколько дней осталось до встречи.\n"
        "📋 /план Купить билеты — добавить план.\n"
        "🎒 /вещь Паспорт — добавить вещь в список.\n"
        "📝 /заметка Не забыть цветы — добавить заметку.\n"
        "📋 /отчет — получить красивый отчет со всеми вашими планами.\n"
        "🏷 /название Дина и Аниша — изменить заголовок в окне.\n"
        "🎨 /стиль #17212b #e91e63 24px italic — изменить дизайн окна.\n\n"
        
        "🗑 <b>4. Удаление:</b>\n"
        "❌ /удалить_план 1 (где 1 — это номер плана в списке)\n"
        "❌ /удалить_вещь 1\n"
        "❌ /удалить_заметку 1\n"
        "🗑 /очистить — удалить вообще все данные.\n\n"
        
        "💡 <b>Совет:</b> Данные теперь хранятся в надежной базе данных, так что они <b>никогда не удалятся</b>, даже если сервер перезагрузится!"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "/мой_код")
async def my_code(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    await message.answer(f"Твой код для приглашения партнера:\n<code>{couple.invite_code}</code>\n\nСсылка:\nhttps://t.me/{(await bot.get_me()).username}?start={couple.invite_code}", parse_mode="HTML")

@dp.message(F.text == "/помощь")
async def help_cmd(message: types.Message):
    text = (
        "💖 <b>Все команды:</b>\n\n"
        "📖 /гайд — подробная инструкция по использованию\n"
        "🎵 /музыка\n📸 /фото\n💌 /любовь\n"
        "📅 /дата 2026-12-31\n❤️ /отношения 2024-01-01\n"
        "📊 /дни\n📋 /план Текст\n🎒 /вещь Текст\n📝 /заметка Текст\n📋 /отчет\n"
        "🏷 /название Имя\n"
        "🎨 /стиль [цвет_фона] [цвет_кнопок] [размер_шрифта] [стиль]\n"
        "👫 /мой_код - получить код для приглашения партнера\n\n"
        "🗑 <b>Удаление:</b>\n"
        "❌ /удалить_план 1\n❌ /удалить_вещь 1\n❌ /удалить_заметку 1\n"
        "🗓 /удалить_дату\n🗑 /очистить"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text.startswith("/стиль "))
async def set_style(message: types.Message):
    parts = message.text.replace("/стиль ", "").split(" ")
    if len(parts) >= 4:
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json
        data["bg_color"] = parts[0]; data["btn_color"] = parts[1]; data["font_size"] = parts[2]; data["font_style"] = parts[3]
        await update_couple_data(couple.id, data)
        await message.answer("✅ Стиль обновлен!", parse_mode="HTML")

@dp.message(F.text == "/музыка")
async def music_cmd(message: types.Message):
    await message.answer_audio(audio=MUSIC_URL, caption="🎵 Наша песня")

@dp.message(F.text.startswith("/название "))
async def set_title(message: types.Message):
    new_title = message.text.replace("/название ", "").strip()
    if new_title:
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json; data["title"] = new_title
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ Название изменено на: <i>{new_title}</i>", parse_mode="HTML")

@dp.message(F.text == "/фото")
async def photo_cmd(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    photo_url = couple.data_json.get("custom_photo") or "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg"
    await message.answer_photo(photo=photo_url, caption="💖 <i>Наша фоточка</i>", parse_mode="HTML")

@dp.message(F.text == "/любовь")
async def love_cmd(message: types.Message):
    quote = random.choice(LOVE_QUOTES)
    await message.answer(f"<blockquote><i>{quote}</i></blockquote>", parse_mode="HTML")

@dp.message(F.text.startswith("/дата "))
async def set_date(message: types.Message):
    try:
        dt = message.text.replace("/дата ", "").strip()
        datetime.datetime.strptime(dt, "%Y-%m-%d")
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json; data["meet_date"] = dt
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ Дата установлена: <b>{dt}</b>", parse_mode="HTML")
    except: await message.answer("❌ Формат: <code>/дата 2026-12-31</code>", parse_mode="HTML")

@dp.message(F.text.startswith("/отношения "))
async def set_rel_date(message: types.Message):
    try:
        dt = message.text.replace("/отношения ", "").strip()
        datetime.datetime.strptime(dt, "%Y-%m-%d")
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json; data["rel_date"] = dt
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ Дата отношений: <b>{dt}</b>", parse_mode="HTML")
    except: await message.answer("❌ Формат: <code>/отношения 2024-01-01</code>", parse_mode="HTML")

@dp.message(F.text == "/дни")
async def days_cmd(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    data = couple.data_json
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        days = (meet - datetime.date.today()).days
        await message.answer(f"💖 До встречи осталось: <b>{days} дн.</b>! 🎆", parse_mode="HTML")
    else: await message.answer("❌ Дата не задана.")

@dp.message(F.text.startswith("/план "))
async def add_plan(message: types.Message):
    plan = message.text.replace("/план ", "").strip()
    if plan:
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json; data["plans"].append({"text": plan, "done": False})
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ План добавлен: <i>{plan}</i>", parse_mode="HTML")

@dp.message(F.text.startswith("/вещь "))
async def add_packing(message: types.Message):
    item = message.text.replace("/вещь ", "").strip()
    if item:
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json; data["packing"].append({"text": item, "done": False})
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ Вещь добавлена: <i>{item}</i>", parse_mode="HTML")

@dp.message(F.text.startswith("/заметка "))
async def add_note(message: types.Message):
    note = message.text.replace("/заметка ", "").strip()
    if note:
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json; data["notes"].append({"text": note, "done": False})
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ Заметка добавлена: <i>{note}</i>", parse_mode="HTML")

@dp.message(F.text == "/отчет")
async def report(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    data = couple.data_json
    title = data.get("title", "💖 Наша пара 💖")
    text = f"<b>{title}</b>\n\n"
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        text += f"✈️ До встречи: <b>{(meet - datetime.date.today()).days} дн.</b>\n"
    if data.get("rel_date"):
        rel = datetime.datetime.strptime(data["rel_date"], "%Y-%m-%d").date()
        text += f"❤️ Вместе: <b>{(datetime.date.today() - rel).days} дн.</b>\n"
    text += "\n<blockquote><b>📋 Планы:</b>\n" + ("\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["plans"], 1)]) if data["plans"] else "  Пусто") + "</blockquote>"
    text += "\n<blockquote><b>🎒 Вещи:</b>\n" + ("\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["packing"], 1)]) if data["packing"] else "  Пусто") + "</blockquote>"
    text += "\n<blockquote><b>📝 Заметки:</b>\n" + ("\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["notes"], 1)]) if data["notes"] else "  Пусто") + "</blockquote>"
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text.startswith("/удалить_план "))
async def del_plan(message: types.Message):
    try:
        idx = int(message.text.replace("/удалить_план ", "").strip()) - 1
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json
        if 0 <= idx < len(data["plans"]):
            removed = data["plans"].pop(idx)
            await update_couple_data(couple.id, data)
            await message.answer(f"✅ Удален план: <i>{removed['text']}</i>", parse_mode="HTML")
    except: await message.answer("❌ Напиши номер: /удалить_план 1")

@dp.message(F.text.startswith("/удалить_вещь "))
async def del_packing(message: types.Message):
    try:
        idx = int(message.text.replace("/удалить_вещь ", "").strip()) - 1
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json
        if 0 <= idx < len(data["packing"]):
            removed = data["packing"].pop(idx)
            await update_couple_data(couple.id, data)
            await message.answer(f"✅ Удалена вещь: <i>{removed['text']}</i>", parse_mode="HTML")
    except: await message.answer("❌ Напиши номер: /удалить_вещь 1")

@dp.message(F.text.startswith("/удалить_заметку "))
async def del_note(message: types.Message):
    try:
        idx = int(message.text.replace("/удалить_заметку ", "").strip()) - 1
        couple = await get_user_couple(message.from_user.id)
        data = couple.data_json
        if 0 <= idx < len(data["notes"]):
            removed = data["notes"].pop(idx)
            await update_couple_data(couple.id, data)
            await message.answer(f"✅ Удалена заметка: <i>{removed['text']}</i>", parse_mode="HTML")
    except: await message.answer("❌ Напиши номер: /удалить_заметку 1")

@dp.message(F.text == "/удалить_дату")
async def del_date(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    data = couple.data_json; data["meet_date"] = None
    await update_couple_data(couple.id, data)
    await message.answer("✅ Дата встречи удалена.")

@dp.message(F.text == "/очистить")
async def clear_all(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    data = couple.data_json
    data["meet_date"] = None; data["plans"] = []; data["packing"] = []; data["notes"] = []
    await update_couple_data(couple.id, data)
    await message.answer("✅ Все данные удалены.")

@dp.inline_query()
async def inline_handler(query: types.InlineQuery):
    text = query.query.lower().strip()
    couple = await get_user_couple(query.from_user.id)
    data = couple.data_json
    results = []
    if "отчет" in text or "фото" in text or not text:
        title = data.get("title", "💖 Наша пара 💖")
        report_text = f"<b>{title}</b>\n\n"
        if data.get("meet_date"):
            meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
            report_text += f"✈️ До встречи: <b>{(meet - datetime.date.today()).days} дн.</b>\n"
        report_text += "\n<blockquote><b>📋 Планы:</b>\n" + ("\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["plans"], 1)]) if data["plans"] else "  Пусто") + "</blockquote>"
        report_text += "\n<blockquote><b>🎒 Вещи:</b>\n" + ("\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["packing"], 1)]) if data["packing"] else "  Пусто") + "</blockquote>"
        report_text += "\n<blockquote><b>📝 Заметки:</b>\n" + ("\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["notes"], 1)]) if data["notes"] else "  Пусто") + "</blockquote>"
        photo_url = data.get("custom_photo") or "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg"
        results.append(InlineQueryResultPhoto(id="report_photo", photo_url=photo_url, thumbnail_url=photo_url, title="📸 Фото + Отчет", description="Фото с отчетом", caption=report_text, parse_mode="HTML"))
    if "окно" in text or "ссылка" in text or not text:
        results.append(InlineQueryResultArticle(id="link_miniapp", title="💖 Открыть Mini App", description="Откроет окно", input_message_content=InputTextMessageContent(message_text=f"💖 Наше окно: {MINI_APP_URL}")))
        results.append(InlineQueryResultArticle(id="link_website", title="🌐 Открыть сайт", description="Откроет сайт", input_message_content=InputTextMessageContent(message_text=f"🌐 Наш сайт: {SERVER_URL}")))
    if "любовь" in text or not text:
        for i, quote in enumerate(LOVE_QUOTES):
            results.append(InlineQueryResultArticle(id=f"quote_{i}", title=f"💌 Цитата {i+1}", description=quote[:40]+"...", input_message_content=InputTextMessageContent(message_text=f"<blockquote><i>{quote}</i></blockquote>", parse_mode="HTML")))
    await query.answer(results[:20], cache_time=1)

async def run_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def startup_event():
    await init_db() 
    asyncio.create_task(run_bot())
