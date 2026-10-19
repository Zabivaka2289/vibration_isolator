"""
Точка входа приложения «Виброизоляция оборудования» (vibration_isolator).

Запуск:  python main.py   →   http://127.0.0.1:8001
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.handlers import router

app = FastAPI(title="Виброизоляция оборудования (vibration_isolator)")

# Статика: CSS, заглушки картинок и медиафайлы виброизоляторов (static/media)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Все страницы и действия описаны в api/handlers.py
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
