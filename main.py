"""
Точка входа приложения «Виброизоляция оборудования» (vibration_isolator).

  ЛР-2: HTML-сайт            → http://127.0.0.1:8001/
  ЛР-3: REST API (JSON)      → http://127.0.0.1:8001/api/vibration_isolators
        документация Swagger → http://127.0.0.1:8001/docs

Запуск:  python main.py
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from api.vibration_isolator_handlers import vibration_isolator_router
from modules.vibration_isolator.controllers.vibration_isolator_controller import vibration_isolator_api_router

vibration_isolator_app = FastAPI(title="Виброизоляция оборудования (vibration_isolator)")

# Статика: CSS, иконки и файлы, загруженные через «Добавить».
# Фото 5 исходных виброизоляторов лежат в MinIO (http://localhost:9000/media/)
vibration_isolator_app.mount("/static", StaticFiles(directory="static"), name="vibration_isolator_static")

# ЛР-2: HTML-страницы (api/vibration_isolator_handlers.py)
vibration_isolator_app.include_router(vibration_isolator_router)

# ЛР-3: REST API с общим префиксом /api (как app.setGlobalPrefix('api') в NestJS)
vibration_isolator_app.include_router(vibration_isolator_api_router, prefix="/api")


@vibration_isolator_app.exception_handler(RequestValidationError)
async def vibration_isolator_validation_handler(request: Request, exc: RequestValidationError):
    """Ошибки валидации DTO в REST API отдаём как в NestJS ValidationPipe:
    статус 400 и понятный список сообщений на русском."""
    if not request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exc)
    messages = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"] if p not in ("body", "query", "path"))
        msg = err["msg"].removeprefix("Value error, ")
        if err["type"] == "missing":
            msg = "обязательное поле"
        elif err["type"] == "extra_forbidden":
            msg = "лишнее поле запрещено"
        elif err["type"].startswith(("int_", "float_")):
            msg = "должно быть числом"
        elif err["type"] == "greater_than_equal":
            msg = f"должно быть не меньше {err['ctx']['ge']}"
        elif err["type"] == "bool_parsing":
            msg = "должно быть true или false"
        messages.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(status_code=400,
                        content={"statusCode": 400, "message": messages, "error": "Bad Request"})


if __name__ == "__main__":
    uvicorn.run("main:vibration_isolator_app", host="127.0.0.1", port=8001, reload=True)
