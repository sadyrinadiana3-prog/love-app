import pytest
import os
import json
import main # Импортируем твой main.py

# Эта функция выполнится перед каждым тестом и создаст чистый файл данных
@pytest.fixture(autouse=True)
def clean_data_file():
    test_file = "webapp_data.json"
    if os.path.exists(test_file):
        os.remove(test_file)
    yield
    if os.path.exists(test_file):
        os.remove(test_file)

def test_load_data_empty():
    # Проверяем, что если файла нет, возвращаются дефолтные данные
    data = main.load_data()
    assert data["title"] == "💖 Аниша и Диша 💖"
    assert data["meet_date"] is None
    assert len(data["plans"]) == 0

def test_save_and_load_data():
    # Проверяем, что данные сохраняются и читаются обратно
    test_data = {
        "title": "Тестовое окно",
        "meet_date": "2026-12-31",
        "plans": [{"text": "Купить билеты", "done": False}],
        "packing": [],
        "notes": [],
        "custom_photo": "test.jpg",
        "bg_color": "#000000",
        "btn_color": "#ffffff",
        "rel_date": "2024-01-01",
        "font_size": "22px",
        "font_style": "italic"
    }
    
    main.save_data(test_data)
    loaded_data = main.load_data()
    
    assert loaded_data["title"] == "Тестовое окно"
    assert loaded_data["plans"][0]["text"] == "Купить билеты"
