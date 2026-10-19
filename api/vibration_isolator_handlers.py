"""
Обработчики (роуты) приложения vibration_isolator.

Адреса:
  GET  /                                   — «Плитка»: каталог + поиск по названию (ORM)
  GET  /filter                             — фильтр по жёсткости (ORM)
  GET  /feed                               — «Лента»: открывает последний просмотренный / первый виброизолятор
  GET  /vibration_isolator/{id}            — карточка в ленте (получение по id через курсор, сырой SQL)
  POST /vibration_isolator/{id}/like       — поставить / снять лайк (ORM)
  POST /vibration_isolator/{id}/delete     — мягкое удаление (курсор, сырой SQL UPDATE)
  GET  /add                                — страница «Добавить»
  POST /add                                — сохранение нового виброизолятора в БД (ORM)

Во всех запросах на чтение учитывается is_deleted = false,
поэтому «удалённые» записи не показываются, но физически остаются в таблице.
"""
import os
import uuid

from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from models.vibration_isolator import VibrationIsolator
from models.like import Like

vibration_isolator_router = APIRouter()
vibration_isolator_templates = Jinja2Templates(directory="templates")

# Тестовый пользователь, от имени которого ставятся лайки (users.id = 1)
VIBRATION_ISOLATOR_USER_ID = 1

# Куда сохраняются фото/видео, загруженные на странице «Добавить»
# (готовые фото 5 виброизоляторов лежат в MinIO: http://localhost:9000/media/...)
VIBRATION_ISOLATOR_UPLOAD_DIR = os.path.join("static", "vibration_isolator_uploads")

# Типы виброизоляторов для выпадающего списка
VIBRATION_ISOLATOR_TYPES = ["Пружинный", "Резинометаллический"]


# ---------------------------------------------------------------------------
# vibration_isolator: Вспомогательные функции
# ---------------------------------------------------------------------------
async def get_vibration_isolator_likes_info(db: AsyncSession):
    """
    Возвращает:
      likes_count — {vibration_isolator_id: количество лайков}
      liked_ids   — множество id, которые лайкнул текущий пользователь
    Оба значения получаются двумя запросами сразу для всех карточек.
    """
    count_rows = await db.execute(
        select(Like.vibration_isolator_id, func.count(Like.id))
        .group_by(Like.vibration_isolator_id)
    )
    likes_count = {row[0]: row[1] for row in count_rows.all()}

    liked_rows = await db.execute(
        select(Like.vibration_isolator_id).where(Like.user_id == VIBRATION_ISOLATOR_USER_ID)
    )
    liked_ids = {row[0] for row in liked_rows.all()}
    return likes_count, liked_ids


def vibration_isolator_safe_redirect(next_url: str) -> RedirectResponse:
    """Редирект только на внутренние адреса сайта (защита от подмены next)."""
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/"
    return RedirectResponse(url=next_url, status_code=303)


async def save_vibration_isolator_upload(file: UploadFile | None) -> str | None:
    """Сохраняет загруженный файл в static/vibration_isolator_uploads и возвращает его адрес (или None)."""
    if file is None or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    name = f"upload_vibration_isolator_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(VIBRATION_ISOLATOR_UPLOAD_DIR, exist_ok=True)
    with open(os.path.join(VIBRATION_ISOLATOR_UPLOAD_DIR, name), "wb") as out:
        out.write(await file.read())
    return f"/static/vibration_isolator_uploads/{name}"


# ---------------------------------------------------------------------------
# vibration_isolator: Плитка (каталог) + поиск — ORM
# ---------------------------------------------------------------------------
@vibration_isolator_router.get("/")
async def get_vibration_isolator_catalog(request: Request, search: str = "", db: AsyncSession = Depends(get_db)):
    stmt = select(VibrationIsolator).where(VibrationIsolator.is_deleted == False)  # noqa: E712
    if search:
        # ilike — регистронезависимый поиск по части названия (PostgreSQL)
        stmt = stmt.where(VibrationIsolator.title.ilike(f"%{search}%"))
    stmt = stmt.order_by(VibrationIsolator.id)

    result = await db.execute(stmt)
    vibration_isolators = result.scalars().all()  # список объектов VibrationIsolator

    likes_count, liked_ids = await get_vibration_isolator_likes_info(db)

    return vibration_isolator_templates.TemplateResponse(
        request=request,
        name="vibration_isolator_index.html",
        context={
            "title": "Виброизоляция",
            "vibration_isolators": vibration_isolators,
            "search": search,
            "likes_count": likes_count,
            "liked_ids": liked_ids,
        },
    )


# ---------------------------------------------------------------------------
# vibration_isolator: Фильтр по жёсткости — ORM
# ---------------------------------------------------------------------------
@vibration_isolator_router.get("/filter")
async def filter_vibration_isolators(
    request: Request,
    min_stiffness: int = 20,
    max_stiffness: int = 80,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(VibrationIsolator)
        .where(VibrationIsolator.is_deleted == False)  # noqa: E712
        .where(VibrationIsolator.stiffness.between(min_stiffness, max_stiffness))
        .order_by(VibrationIsolator.id)
    )
    result = await db.execute(stmt)
    vibration_isolators = result.scalars().all()
    likes_count, liked_ids = await get_vibration_isolator_likes_info(db)

    return vibration_isolator_templates.TemplateResponse(
        request=request,
        name="vibration_isolator_filter.html",
        context={
            "vibration_isolators": vibration_isolators,
            "min_stiffness": min_stiffness,
            "max_stiffness": max_stiffness,
            "likes_count": likes_count,
            "liked_ids": liked_ids,
        },
    )


# ---------------------------------------------------------------------------
# vibration_isolator: Лента
# ---------------------------------------------------------------------------
@vibration_isolator_router.get("/feed")
async def get_vibration_isolator_feed(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Открывает ленту: последнюю просмотренную карточку (запоминается в cookie),
    если её нет или она удалена — первую по порядку.
    """
    ids_result = await db.execute(
        select(VibrationIsolator.id)
        .where(VibrationIsolator.is_deleted == False)  # noqa: E712
        .order_by(VibrationIsolator.id)
    )
    active_ids = [row[0] for row in ids_result.all()]
    if not active_ids:
        return RedirectResponse(url="/", status_code=303)

    last_id = request.cookies.get("last_vibration_isolator_id")
    if last_id and last_id.isdigit() and int(last_id) in active_ids:
        return RedirectResponse(url=f"/vibration_isolator/{last_id}", status_code=303)
    return RedirectResponse(url=f"/vibration_isolator/{active_ids[0]}", status_code=303)


@vibration_isolator_router.get("/vibration_isolator/{vibration_isolator_id}")
async def get_vibration_isolator_detail(
    request: Request, vibration_isolator_id: int, db: AsyncSession = Depends(get_db)
):
    # Получение записи по id через курсор (сырой SQL)
    row = (
        await db.execute(
            text("""
                SELECT id, title, type, stiffness, freq, description, image_url, video_url
                FROM vibration_isolators
                WHERE id = :id AND is_deleted = false
            """),
            {"id": vibration_isolator_id},
        )
    ).mappings().fetchone()  # fetchone() — одна строка или None

    if row is None:
        return vibration_isolator_templates.TemplateResponse(
            request=request,
            name="vibration_isolator_404.html",
            context={"message": "Виброизолятор не найден"},
            status_code=404,
        )

    # id следующей карточки для кнопки «Далее» (по кругу)
    ids_result = await db.execute(
        select(VibrationIsolator.id)
        .where(VibrationIsolator.is_deleted == False)  # noqa: E712
        .order_by(VibrationIsolator.id)
    )
    active_ids = [r[0] for r in ids_result.all()]
    pos = active_ids.index(vibration_isolator_id)
    next_id = active_ids[(pos + 1) % len(active_ids)]

    likes_count, liked_ids = await get_vibration_isolator_likes_info(db)

    response = vibration_isolator_templates.TemplateResponse(
        request=request,
        name="vibration_isolator_feed.html",
        context={
            "vibration_isolator": row,
            "next_id": next_id,
            "position": pos + 1,
            "total": len(active_ids),
            "likes_count": likes_count.get(vibration_isolator_id, 0),
            "is_liked": vibration_isolator_id in liked_ids,
        },
    )
    # Запоминаем последнюю просмотренную карточку для кнопки «Лента»
    response.set_cookie("last_vibration_isolator_id", str(vibration_isolator_id))
    return response


# ---------------------------------------------------------------------------
# vibration_isolator: Лайк — ORM
# ---------------------------------------------------------------------------
@vibration_isolator_router.post("/vibration_isolator/{vibration_isolator_id}/like")
async def like_vibration_isolator(
    vibration_isolator_id: int,
    user_id: int = Form(...),
    next: str = Form("/"),
    db: AsyncSession = Depends(get_db),
):
    # Есть ли уже лайк этого пользователя на этот виброизолятор
    stmt = select(Like).where(
        Like.user_id == user_id,
        Like.vibration_isolator_id == vibration_isolator_id,
    )
    existing_like = (await db.execute(stmt)).scalar_one_or_none()

    if existing_like:
        await db.delete(existing_like)          # лайк был — снимаем
    else:
        db.add(Like(user_id=user_id, vibration_isolator_id=vibration_isolator_id))  # ставим

    await db.commit()
    # Возвращаем пользователя туда, откуда он нажал (Плитка / Фильтр / Лента)
    return vibration_isolator_safe_redirect(next)


# ---------------------------------------------------------------------------
# vibration_isolator: Мягкое удаление — курсор (сырой SQL)
# ---------------------------------------------------------------------------
@vibration_isolator_router.post("/vibration_isolator/{vibration_isolator_id}/delete")
async def delete_vibration_isolator(
    vibration_isolator_id: int,
    next: str = Form("/"),
    db: AsyncSession = Depends(get_db),
):
    # Не DELETE, а UPDATE флага: запись остаётся в таблице, но больше не показывается
    await db.execute(
        text("""
            UPDATE vibration_isolators
            SET is_deleted = true
            WHERE id = :id
        """),
        {"id": vibration_isolator_id},
    )
    await db.commit()
    return vibration_isolator_safe_redirect(next)


# ---------------------------------------------------------------------------
# vibration_isolator: Добавление — ORM
# ---------------------------------------------------------------------------
@vibration_isolator_router.get("/add")
async def get_vibration_isolator_add_page(request: Request):
    return vibration_isolator_templates.TemplateResponse(
        request=request,
        name="vibration_isolator_add.html",
        context={"title": "Добавить виброизолятор", "types": VIBRATION_ISOLATOR_TYPES},
    )


@vibration_isolator_router.post("/add")
async def add_vibration_isolator(
    # Обязательные поля
    title: str = Form(...),
    type: str = Form(...),
    stiffness: int = Form(...),
    freq: float = Form(...),
    # Необязательные поля
    description: str = Form(""),
    photo: UploadFile | None = File(None),
    video: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    new_item = VibrationIsolator(
        title=title.strip(),
        type=type,
        stiffness=stiffness,
        freq=freq,
        description=description.strip() or None,
        image_url=await save_vibration_isolator_upload(photo),
        video_url=await save_vibration_isolator_upload(video),
        is_deleted=False,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)  # получаем id, который выдала БД
    # Сразу открываем новую карточку в ленте
    return RedirectResponse(url=f"/vibration_isolator/{new_item.id}", status_code=303)
