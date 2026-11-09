from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI()
DATA_FILE = "webapp_data.json"

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
            let res = await fetch('/api/data');
            currentData = await res.json(); updateUI();
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
