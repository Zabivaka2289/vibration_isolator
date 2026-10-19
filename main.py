"""
Точка входа приложения «Виброизоляция оборудования» (vibration_isolator).

Запуск:  python main.py   →   http://127.0.0.1:8001
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.vibration_isolator_handlers import vibration_isolator_router

vibration_isolator_app = FastAPI(title="Виброизоляция оборудования (vibration_isolator)")

# Статика: CSS, иконки и файлы, загруженные через «Добавить».
# Фото 5 исходных виброизоляторов лежат в MinIO (http://localhost:9000/media/)
vibration_isolator_app.mount("/static", StaticFiles(directory="static"), name="vibration_isolator_static")

# Все страницы и действия описаны в api/vibration_isolator_handlers.py
vibration_isolator_app.include_router(vibration_isolator_router)

if __name__ == "__main__":
    uvicorn.run("main:vibration_isolator_app", host="127.0.0.1", port=8001, reload=True)
