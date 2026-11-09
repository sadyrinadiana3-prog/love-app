from fastapi import FastAPI, Request
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

@app.get("/", response_class=HTMLResponse)
async def index():
    # Эта строка говорит серверу искать index.html в той же папке, где лежит main.py
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/data")
async def get_data():
    return load_data()

@app.post("/api/data")
async def update_data(request: Request):
    new_data = await request.json()
    save_data(new_data)
    return {"status": "ok"}
