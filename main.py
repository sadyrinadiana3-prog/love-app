from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (InlineKeyboardButton, WebAppInfo, InlineQueryResultArticle, 
                           InlineQueryResultPhoto, InputTextMessageContent, InlineQueryResultsButton,
                           LabeledPrice, PreCheckoutQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import datetime
import random
import asyncio
import uuid
import os
import logging

from database import init_db, async_session, Couple
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVER_URL = "https://love-app-rb47.onrender.com"
MUSIC_URL = "https://example.com/love.mp3"

bot = Bot(token=BOT_TOKEN if BOT_TOKEN else "123:fake")
dp = Dispatcher()

LOVE_QUOTES = [
    "«Расстояние — причина для боли, но не причина для измен.»",
    "«Для честной любви даже самое маленькое расстояние — слишком большое, но даже самое большое расстояние — преодолимо.»",
]

DAILY_QUESTIONS = [
    "Что ты ценишь в партнере больше всего?",
    "Какой ваш самый счастливый момент вместе?",
    "Что бы ты хотел сделать вместе в следующем году?",
    "За что ты благодарен партнеру сегодня?",
]

# --- РАБОТА С БАЗОЙ ---
async def get_user_couple(user_id: int, create_if_missing=True):
    async with async_session() as session:
        try:
            result = await session.execute(select(Couple).where((Couple.user1_id == user_id) | (Couple.user2_id == user_id)))
            couple = result.scalars().first()
            
            if not couple and create_if_missing:
                new_code = f"LOVE-{uuid.uuid4().hex[:4].upper()}"
                couple = Couple(user1_id=user_id, invite_code=new_code, data_json={
                    "meet_date": None, "plans": [], "packing": [], "notes": [], 
                    "custom_photo": "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg", 
                    "title": "💖 Наша пара 💖",
                    "bg_color": "#17212b", "btn_color": "#2481cc", 
                    "rel_date": None, "font_size": "22px", "font_style": "italic",
                    "capsules": [],
                    "daily_question": None,
                    "partner_answer": None
                })
                session.add(couple)
                await session.commit()
                await session.refresh(couple)
            return couple
        except Exception as e:
            logger.error(f"Ошибка базы данных для user_id {user_id}: {e}")
            await session.rollback()
            new_code = f"LOVE-{uuid.uuid4().hex[:4].upper()}"
            couple = Couple(user1_id=user_id, invite_code=new_code, data_json={})
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
        .palette { display: flex; gap: 5px; flex-wrap: wrap; margin: 10px 0; justify-content: center; }
        .color-dot { width: 30px; height: 30px; border-radius: 50%; border: 2px solid white; cursor: pointer; }
        .color-dot:active { transform: scale(0.9); }
        .danger-btn { background: #e53935; margin-top: 20px; }
        .premium-btn { background: linear-gradient(45deg, #ff9800, #e91e63); margin-top: 20px; }
        .premium-section { border: 2px dashed #ff9800; padding: 10px; border-radius: 10px; margin-top: 20px; }
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
        <p><b>Название окна:</b></p>
        <input type="text" id="titleInput" placeholder="Например: Дина и Аниша">
        <button onclick="updateTitle()" style="background:#ff9800;">Изменить название</button>
        
        <p><b>Цвет фона:</b></p>
        <div class="palette" id="bgPalette"></div>
        <input type="text" id="bgColor" placeholder="Или введи вручную">
        
        <p><b>Цвет кнопок:</b></p>
        <div class="palette" id="btnPalette"></div>
        <input type="text" id="btnColor" placeholder="Или введи вручную">
        
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
        <button onclick="unlinkPartner()" class="danger-btn">🗑 Отвязать партнёра</button>
        
        <div class="premium-section">
            <h3>💎 Премиум</h3>
            <p id="premiumStatus">Проверка статуса...</p>
            <button onclick="buyPremium()" class="premium-btn" id="buyPremiumBtn" style="display:none;">Купить Премиум за 50 Stars</button>
        </div>
    </div>
    <script>
        let tg = window.Telegram.WebApp; tg.expand();
        let currentData = {};
        let alertShown = false;
        let userId = tg.initDataUnsafe?.user?.id || 0;
        let isPremium = false;

        const colors = ['#17212b', '#000000', '#1e3a5f', '#2e4a62', '#4a2e62', '#623a4a', '#2e6244', '#ffffff', '#e91e63', '#ff9800', '#4caf50', '#2481cc'];
        const premiumColors = ['#ff6b6b', '#feca57', '#48dbfb', '#ff9ff3', '#54a0ff'];

        function renderPalette(containerId, inputId, includePremium = false) {
            const container = document.getElementById(containerId);
            let allColors = colors;
            if (includePremium && isPremium) {
                allColors = colors.concat(premiumColors);
            }
            container.innerHTML = '';
            allColors.forEach(color => {
                const dot = document.createElement('div');
                dot.className = 'color-dot';
                dot.style.backgroundColor = color;
                dot.onclick = () => { document.getElementById(inputId).value = color; };
                container.appendChild(dot);
            });
        }

        async function loadData() {
            let res = await fetch(`/api/data?user_id=${userId}`); 
            currentData = await res.json(); 
            
            let premRes = await fetch(`/api/premium_status?user_id=${userId}`);
            let premData = await premRes.json();
            isPremium = premData.is_premium;
            
            updateUI();
            renderPalette('bgPalette', 'bgColor', true);
            renderPalette('btnPalette', 'btnColor', true);
            
            document.getElementById('premiumStatus').innerText = isPremium ? "✅ Премиум активен! Вам доступны эксклюзивные цвета." : "❌ Премиум не активен.";
            document.getElementById('buyPremiumBtn').style.display = isPremium ? 'none' : 'block';
        }

        function updateUI() {
            if (currentData.title) { 
                document.getElementById('appTitle').innerText = currentData.title; 
                document.getElementById('titleInput').value = currentData.title;
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

        async function buyPremium() {
            tg.showAlert("Для покупки перейдите в чат с ботом и напишите /premium");
        }

        async function saveData() {
            await fetch(`/api/data?user_id=${userId}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(currentData) });
            updateUI();
        }
        
        async function setDate() { let val = document.getElementById('dateInput').value; if (!val) return; currentData.meet_date = val; await saveData(); }
        async function setRelDate() { let val = document.getElementById('relDateInput').value; if (!val) return; currentData.rel_date = val; await saveData(); }
        async function updateTitle() { let newTitle = document.getElementById('titleInput').value; if (newTitle.trim()) { currentData.title = newTitle; await saveData(); tg.showAlert("✅ Название изменено!"); } }
        async function unlinkPartner() { if (confirm("Отвязать партнёра?")) { await fetch(`/api/unlink?user_id=${userId}`, { method: 'POST' }); tg.showAlert("✅ Партнёр отвязан."); loadData(); } }
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
        function showAlert() { if (currentData.meet_date) { let meet = new Date(currentData.meet_date); let today = new Date(); let diff = Math.ceil((meet - today) / (1000 * 60 * 60 * 24)); tg.showAlert(`💖 До встречи: ${diff} дн.!`); } else { tg.showAlert("Дата не задана"); } }
        
        loadData();
    </script>
</body>
</html>
"""

# --- API ДЛЯ ПРЕМИУМА ---
@app.get("/api/premium_status")
async def premium_status(user_id: int):
    couple = await get_user_couple(user_id)
    return {"is_premium": couple.is_premium}

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

@app.post("/api/unlink")
async def unlink_partner(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Couple).where((Couple.user1_id == user_id) | (Couple.user2_id == user_id)))
        couple = result.scalar_one_or_none()
        if couple:
            if couple.user1_id == user_id:
                couple.user1_id = couple.user2_id
                couple.user2_id = None
            else:
                couple.user2_id = None
            await session.commit()
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
            await message.answer("🎉 Вы связаны! Открывайте окно!")
        elif couple and couple.user1_id == user_id:
            await message.answer("Это ваш код.")
        else:
            await message.answer("❌ Код не найден.")
            await get_user_couple(user_id) 

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=SERVER_URL)))
    await message.answer("Нажми на кнопку ниже.", reply_markup=builder.as_markup())

# --- ОБНОВЛЕННЫЙ START ---
@dp.message(CommandStart())
async def start(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=SERVER_URL)))
    
    premium_status = "✅ У вас есть Премиум!" if couple.is_premium else "💎 У вас нет Премиума."
    
    text = (
        f"Привет! Твой код приглашения для партнера:\n"
        f"<code>{couple.invite_code}</code>\n\n"
        f"Скинь его партнеру или отправь ссылку:\n"
        f"https://t.me/{(await bot.get_me()).username}?start={couple.invite_code}\n\n"
        f"<b>💎 Премиум:</b>\n"
        f"• /premium — узнать все подробности о функциях\n"
        f"• /buy_premium — купить Премиум за 50 Stars\n"
        f"• Статус: {premium_status}\n\n"
        f"<b>🛠 Основные команды:</b>\n"
        f"📅 /дата 2026-12-31\n"
        f"❤️ /отношения 2024-01-01\n"
        f"📊 /дни\n"
        f"📋 /план Текст\n"
        f"🎒 /вещь Текст\n"
        f"📝 /заметка Текст\n"
        f"📋 /отчет\n"
        f"👫 /мой_код — получить код\n\n"
        f"<i>Если не знаешь, что делать, напиши /гайд</i>"
    )
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ПРЕМИУМ (ИНФОРМАЦИЯ) ---
@dp.message(F.text == "/premium")
async def premium_cmd(message: types.Message):
    text = (
        "💎 <b>Премиум-подписка Love App</b>\n\n"
        "Нажмите на кнопку ниже, чтобы узнать все подробности и функции."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="ℹ️ Подробнее о функциях", callback_data="premium_details"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "premium_details")
async def premium_details(callback: types.CallbackQuery):
    text = (
        "💎 <b>Что дает Премиум в Love App и как этим пользоваться?</b>\n\n"
        "🎨 <b>1. Эксклюзивный дизайн:</b>\n"
        "Зайди в Mini App (Окно). Прокрути вниз до раздела «Цвет фона». Там появятся 5 новых ярких цветов. Нажми на любой и «Применить всё».\n\n"
        "⏳ <b>2. Капсула времени:</b>\n"
        "Напиши в чат команду <code>/капсула</code>. Бот попросит дату и текст. В нужный день он пришлет это сообщение вам обоим.\n\n"
        "❓ <b>3. Ежедневные вопросы:</b>\n"
        "Напиши команду <code>/вопрос</code>. Бот пришлет вопрос. Ответь на него командой <code>/ответ Твой текст</code>. Как только партнер тоже ответит, вы увидите ответы друг друга.\n\n"
        "📊 <b>4. Аналитика и Экспорт:</b>\n"
        "Эти функции находятся в разработке и скоро появятся в Mini App.\n\n"
        "Стоимость: <b>50 Stars</b> (навсегда)."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=None)
    await callback.answer()

# --- ОТДЕЛЬНАЯ КОМАНДА ДЛЯ ПОКУПКИ ---
@dp.message(F.text == "/buy_premium")
async def buy_premium_cmd(message: types.Message):
    text = (
        "💎 <b>Покупка Премиум-подписки</b>\n\n"
        "Нажмите на кнопку ниже, чтобы оплатить подписку через Telegram Stars."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⭐ Оплатить 50 Stars", pay=True))
    
    prices = [LabeledPrice(label="XTR", amount=50)]
    await message.answer_invoice(
        title="Премиум Love App",
        description="Эксклюзивные цвета, капсулы времени и другие функции.",
        prices=prices,
        provider_token="",
        payload="premium_50",
        currency="XTR",
        reply_markup=builder.as_markup()
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def success_payment(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    async with async_session() as session:
        result = await session.execute(select(Couple).where(Couple.id == couple.id))
        c = result.scalar_one_or_none()
        if c:
            c.is_premium = True
            await session.commit()
    await message.answer("🎉 <b>Оплата прошла успешно!</b> Премиум активирован навсегда. Откройте окно, чтобы увидеть новые цвета!", parse_mode="HTML")

# --- СЕКРЕТНАЯ КОМАНДА ДЛЯ ВЛАДЕЛЬЦА ---
@dp.message(F.text == "/L0v3_Adm1n_Pr3m1um_2026_X9z")
async def admin_premium(message: types.Message):
    if message.from_user.id != 1169264429:
        await message.answer("❌ У вас нет доступа к этой команде.")
        return
    
    couple = await get_user_couple(message.from_user.id)
    async with async_session() as session:
        result = await session.execute(select(Couple).where(Couple.id == couple.id))
        c = result.scalar_one_or_none()
        if c:
            c.is_premium = True
            await session.commit()
    await message.answer("🎉 <b>Админ-доступ:</b> Премиум активирован навсегда для вашего аккаунта!", parse_mode="HTML")

# --- НОВЫЕ ПРЕМИУМ-КОМАНДЫ ---
@dp.message(F.text == "/капсула")
async def capsule_cmd(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    if not couple.is_premium:
        await message.answer("❌ Эта функция доступна только с Премиумом. Напиши /premium.")
        return
    await message.answer("⏳ <b>Создание капсулы времени</b>\n\nНапиши дату (в формате ГГГГ-ММ-ДД), когда должно открыться сообщение, и через пробел текст.\n\nПример: <code>/капсула 2026-12-31 С Новым Годом, любимая!</code>", parse_mode="HTML")

@dp.message(F.text.startswith("/капсула "))
async def create_capsule(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    if not couple.is_premium:
        return
    try:
        parts = message.text.replace("/капсула ", "").split(" ", 1)
        date_str = parts[0]
        text_msg = parts[1]
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        data = couple.data_json
        if "capsules" not in data:
            data["capsules"] = []
        data["capsules"].append({"date": date_str, "text": text_msg, "sent": False})
        await update_couple_data(couple.id, data)
        await message.answer(f"✅ Капсула создана! Она откроется {date_str}.", parse_mode="HTML")
    except:
        await message.answer("❌ Ошибка формата. Пример: <code>/капсула 2026-12-31 Текст</code>", parse_mode="HTML")

@dp.message(F.text == "/вопрос")
async def daily_question(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    if not couple.is_premium:
        await message.answer("❌ Эта функция доступна только с Премиумом. Напиши /premium.")
        return
    
    question = random.choice(DAILY_QUESTIONS)
    data = couple.data_json
    data["daily_question"] = question
    data["partner_answer"] = None
    await update_couple_data(couple.id, data)
    
    await message.answer(f"❓ <b>Вопрос дня:</b>\n\n{question}\n\nОтветьте на него командой <code>/ответ Твой текст</code>", parse_mode="HTML")

@dp.message(F.text.startswith("/ответ "))
async def answer_question(message: types.Message):
    couple = await get_user_couple(message.from_user.id)
    if not couple.is_premium:
        return
    answer = message.text.replace("/ответ ", "").strip()
    data = couple.data_json
    if data.get("partner_answer"):
        await message.answer("❌ Ваш партнер уже ответил на этот вопрос.")
        return
    
    data["partner_answer"] = answer
    await update_couple_data(couple.id, data)
    await message.answer("✅ Ваш ответ сохранен! Теперь партнер тоже может ответить.")

# --- ОСТАЛЬНЫЕ КОМАНДЫ (гайд, план, отчет и т.д.) ---
@dp.message(F.text == "/гайд")
async def guide(message: types.Message):
    text = (
        "📖 <b>Гайд по боту Love App</b>\n\n"
        "👫 <b>1. Как пригласить партнера?</b>\n"
        "• Напиши /мой_код.\n"
        "• Скопируй ссылку и отправь партнеру.\n\n"
        "💻 <b>2. Mini App</b>\n"
        "• Жми «💖 Открыть наше окно» и добавляй планы.\n"
        "• Внизу окна есть палитра цветов и кнопка отвязки.\n\n"
        "🛠 <b>3. Команды:</b>\n"
        "📅 /дата 2026-12-31\n❤️ /отношения 2024-01-01\n📊 /дни\n📋 /план Текст\n🎒 /вещь Текст\n📝 /заметка Текст\n📋 /отчет\n🏷 /название Имя\n🎨 /стиль #17212b #e91e63 24px italic\n\n"
        "💎 <b>4. Премиум:</b>\n"
        "Напиши /premium, чтобы узнать о премиум-функциях.\n"
        "Напиши /buy_premium, чтобы купить.\n"
        "После активации доступны: /капсула, /вопрос.\n\n"
        "🗑 <b>5. Удаление:</b>\n"
        "❌ /удалить_план 1\n❌ /удалить_вещь 1\n❌ /удалить_заметку 1\n🗑 /очистить"
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
        "📖 /гайд — подробная инструкция\n"
        "🎵 /музыка\n📸 /фото\n💌 /любовь\n"
        "📅 /дата 2026-12-31\n❤️ /отношения 2024-01-01\n"
        "📊 /дни\n📋 /план Текст\n🎒 /вещь Текст\n📝 /заметка Текст\n📋 /отчет\n"
        "🏷 /название Имя\n"
        "🎨 /стиль [цвет_фона] [цвет_кнопок] [размер_шрифта] [стиль]\n"
        "👫 /мой_код - получить код для приглашения партнера\n"
        "💎 /premium - узнать о премиуме\n"
        "🛒 /buy_premium - купить премиум\n"
        "⏳ /капсула - создать капсулу времени (премиум)\n"
        "❓ /вопрос - вопрос дня (премиум)\n"
        "✍️ /ответ - ответить на вопрос (премиум)\n\n"
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

# --- INLINE РЕЖИМ ---
@dp.inline_query()
async def inline_handler(query: types.InlineQuery):
    text = query.query.lower().strip()
    couple = await get_user_couple(query.from_user.id, create_if_missing=False)
    
    if not couple:
        await query.answer([], cache_time=1, switch_pm_text="Сначала напиши боту /start", switch_pm_parameter="start")
        return

    data = couple.data_json
    results = []
    bot_username = (await bot.get_me()).username

    meet_text = "Дата не задана"
    if data.get("meet_date"):
        meet = datetime.datetime.strptime(data["meet_date"], "%Y-%m-%d").date()
        days = (meet - datetime.date.today()).days
        meet_text = f"✈️ До встречи: <b>{days} дн.</b>"
    
    rel_text = "Дата не задана"
    if data.get("rel_date"):
        rel = datetime.datetime.strptime(data["rel_date"], "%Y-%m-%d").date()
        days = (datetime.date.today() - rel).days
        rel_text = f"❤️ Вместе уже: <b>{days} дн.</b>"

    plans_text = "\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["plans"], 1)]) if data["plans"] else "  Пусто"
    packing_text = "\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["packing"], 1)]) if data["packing"] else "  Пусто"
    notes_text = "\n".join([f"  {'✅' if p.get('done') else '🔸'} {i}. {p.get('text')}" for i, p in enumerate(data["notes"], 1)]) if data["notes"] else "  Пусто"

    title = data.get("title", "💖 Наша пара 💖")
    photo_url = data.get("custom_photo") or "https://i.ibb.co/LhH0r3tQ/IMG-20261108-024248-959.jpg"

    if not text or "фото" in text or "отчет" in text:
        caption = (
            f"<b>{title}</b>\n\n"
            f"{meet_text}\n{rel_text}\n\n"
            f"<blockquote><b>📋 Планы:</b>\n{plans_text}</blockquote>\n"
            f"<blockquote><b>🎒 Вещи:</b>\n{packing_text}</blockquote>\n"
            f"<blockquote><b>📝 Заметки:</b>\n{notes_text}</blockquote>"
        )
        results.append(InlineQueryResultPhoto(
            id="report_photo", photo_url=photo_url, thumbnail_url=photo_url, 
            title="📸 Наше фото + Отчет", description="Красивая карточка", 
            caption=caption, parse_mode="HTML"
        ))

    if not text or "дата" in text or "дни" in text:
        dates_text = f"<b>{title}</b>\n\n{meet_text}\n{rel_text}\n\n<i>Нажми на кнопку ниже!</i>"
        results.append(InlineQueryResultArticle(
            id="dates_info", title="📅 Даты и Уведомление", 
            description="Сколько дней осталось", 
            input_message_content=InputTextMessageContent(message_text=dates_text, parse_mode="HTML")
        ))

    if not text or "код" in text:
        code_text = f"💖 <b>Мой код:</b>\n<code>{couple.invite_code}</code>\n\nСсылка:\nhttps://t.me/{bot_username}?start={couple.invite_code}"
        results.append(InlineQueryResultArticle(
            id="my_code", title="👫 Мой код и Ссылка", 
            description="Отправит код партнеру", 
            input_message_content=InputTextMessageContent(message_text=code_text, parse_mode="HTML")
        ))

    if not text or "гайд" in text:
        guide_text = "📖 <b>Гайд:</b> /дата, /план, /вещь, /отчет, /premium"
        results.append(InlineQueryResultArticle(
            id="guide", title="📖 Гайд", description="Инструкция", 
            input_message_content=InputTextMessageContent(message_text=guide_text, parse_mode="HTML")
        ))

    inline_button = InlineQueryResultsButton(text="💖 Открыть наше окно", web_app=WebAppInfo(url=SERVER_URL))
    await query.answer(results[:10], cache_time=1, button=inline_button)

async def run_bot():
    logger.info("Запуск polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")

@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(run_bot())