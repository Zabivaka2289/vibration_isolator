# vibration_isolator — «Виброизоляция оборудования»

Лабораторная работа №2 по РИП: FastAPI + PostgreSQL (Docker) + SQLAlchemy + Alembic + Pydantic Settings.
Предметная область — каталог виброизоляторов (услуга = `vibration_isolator`).

## Запуск

```bash
# 1. База данных PostgreSQL + Adminer в Docker
docker-compose up -d

# 2. Виртуальное окружение и зависимости
python -m venv venv
venv\Scripts\activate            # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt

# 3. Создание таблиц миграцией
alembic upgrade head

# 4. Начальные данные: открыть Adminer http://localhost:8081
#    (система PostgreSQL, сервер postgres, пользователь vibration_isolator_user,
#     пароль vibration_isolator_password, БД vibration_isolator_db)
#    → «SQL-команда» → вставить содержимое sql/seed.sql → «Выполнить»

# 5. Сайт
python main.py                   # http://127.0.0.1:8001
# MinIO с фотографиями (http://localhost:9000) тоже должен быть запущен
```

## Структура проекта

```text
vibration_isolator/
├── alembic/
│   ├── versions/0001_init_vibration_isolators_users_likes.py  — миграция: 3 таблицы
│   ├── env.py                — Alembic берёт адрес БД из .env и модели из models/
│   └── script.py.mako        — шаблон новых миграций
├── alembic.ini               — настройки Alembic
├── api/vibration_isolator_handlers.py — все страницы и действия (роуты)
├── core/config.py            — чтение .env через pydantic-settings
├── db/base.py                — базовый класс моделей
├── db/session.py             — подключение к БД, сессия на каждый запрос
├── models/
│   ├── vibration_isolator.py — модель VibrationIsolator (таблица vibration_isolators)
│   ├── user.py               — модель User (таблица users)
│   └── like.py               — модель Like (таблица likes)
├── templates/
│   ├── vibration_isolator_base.html   — общий каркас: «телефон» 390×844 + нижнее меню
│   ├── vibration_isolator_card.html   — карточка для Плитки и Фильтра
│   ├── vibration_isolator_index.html  — Плитка + поиск
│   ├── vibration_isolator_filter.html — фильтр по жёсткости
│   ├── vibration_isolator_feed.html   — Лента (одна карточка на экран)
│   ├── vibration_isolator_add.html    — Добавить (сохранение в БД)
│   └── vibration_isolator_404.html    — «не найдено»
├── static/
│   ├── css/vibration_isolator_style.css
│   ├── img/                  — иконки и заглушки «нет фото / нет видео»
│   └── vibration_isolator_uploads/ — файлы, загруженные через «Добавить» (создаётся сама)
├── sql/seed.sql              — начальные данные
├── er/                       — ER-диаграмма (StarUML .mdj + PDF/PNG под A4)
├── docker-compose.yml
├── .env / .env.example
├── .gitignore
├── main.py                 — приложение vibration_isolator_app
└── requirements.txt
```

## Адреса (роуты)

| Метод | Адрес | Что делает | Как работает с БД |
|---|---|---|---|
| GET | `/` | Плитка, поиск `?search=` | ORM, `ILIKE` |
| GET | `/filter` | Фильтр по жёсткости | ORM, `BETWEEN` |
| GET | `/feed` | Открыть Ленту (последняя просмотренная карточка) | ORM |
| GET | `/vibration_isolator/{id}` | Карточка в Ленте | курсор, сырой SQL `SELECT` |
| POST | `/vibration_isolator/{id}/like` | Поставить / снять лайк | ORM |
| POST | `/vibration_isolator/{id}/delete` | Мягкое удаление | курсор, сырой SQL `UPDATE ... SET is_deleted = true` |
| GET | `/add` | Форма добавления | — |
| POST | `/add` | Сохранить новый виброизолятор | ORM `INSERT` |

## Таблицы БД

**vibration_isolators** — услуги

| Поле | Тип | Обязательное |
|---|---|---|
| id | INTEGER, PK | да |
| title | VARCHAR(100) | да |
| type | VARCHAR(50) | да |
| stiffness | INTEGER (Н/мм) | да |
| freq | FLOAT (Гц) | да |
| description | VARCHAR(500) | **нет** (NULL) |
| image_url | VARCHAR(255) | **нет** (NULL) |
| video_url | VARCHAR(255) | **нет** (NULL) |
| is_deleted | BOOLEAN, default false | да |

**users** — `id` (PK), `username` (уникальный).
**likes** — `id` (PK), `user_id` (FK → users.id), `vibration_isolator_id` (FK → vibration_isolators.id).

Поля `created_at` нет ни в одной таблице.

---

## Пояснения к исправлениям по замечаниям

### 1. Всё переименовано в `vibration_isolator`
Слов `hotel` / `isolator` / `vibro` в коде больше нет:
- папка проекта `vibration_isolator/`;
- модель `VibrationIsolator`, файл `models/vibration_isolator.py`, таблица `vibration_isolators`,
  внешний ключ `likes.vibration_isolator_id`;
- шаблоны `templates/vibration_isolator_*.html` (Лента — `vibration_isolator_feed.html`, был `hotel.html`);
- файл роутов `api/vibration_isolator_handlers.py`, объекты `vibration_isolator_router`,
  `vibration_isolator_templates`, `vibration_isolator_app`; все функции-обработчики содержат
  `vibration_isolator` (`get_vibration_isolator_catalog`, `get_vibration_isolator_feed` …);
- JS-функции `vibrationIsolatorChangeMedia`, `vibrationIsolatorToggleDescription`,
  `vibrationIsolatorBindPreview`; стили `vibration_isolator_style.css`;
- каждый раздел (отдел) кода подписан `vibration_isolator: …` — в Python, CSS и JS;
- адреса `/vibration_isolator/{id}`, `/vibration_isolator/{id}/like`, `/vibration_isolator/{id}/delete`
  (было `/isolator/{id}`);
- переменные в коде и шаблонах: `vibration_isolators`, `vibration_isolator_id`;
- БД `vibration_isolator_db`, пользователь `vibration_isolator_user`, контейнеры
  `vibration_isolator_postgres` / `vibration_isolator_adminer`, том `vibration_isolator_pgdata`;
- фото и видео 5 исходных записей берутся из MinIO (`http://localhost:9000/media/vibro1.png …`);
- cookie последней карточки `last_vibration_isolator_id`.

### 2. Фиксированный размер телефона, без адаптивности
Раньше страница растягивалась на весь экран (`width: 100vw; height: 100vh`) и были `@media`-правила.
Теперь всё содержимое лежит в блоке `.phone` фиксированного размера **390 × 844 px**
(`templates/vibration_isolator_base.html`, `static/css/vibration_isolator_style.css`). Все `@media` удалены, нижнее меню и шапки
позиционируются внутри «телефона», а не по окну браузера. Размер меняется в одном месте —
переменные `--phone-w` / `--phone-h` в начале `vibration_isolator_style.css`.

### 3. Лента: описание справа
Блок с названием, жёсткостью, частотой, текстом и типом (`.description-overlay`) прижат к правому
краю и выровнен по правому краю (`align-items: flex-end; text-align: right`).
Кнопки «лайк» и «Далее» стоят справа над описанием и не перекрывают его.

### 4. Картинки на обоих состояниях в «Добавить»
- Кнопки «Фото» и «Видео» — это `<label>` с иконкой. До выбора файла показывается иконка,
  после выбора — превью файла **внутри той же кнопки**, иконка остаётся маленькой в углу,
  кнопку можно нажать ещё раз, чтобы заменить файл.
- Исправлена ошибка: раньше выбор фото делал `innerHTML = ...` и стирал превью видео.
  Теперь у фото и видео свои независимые превью.
- Иконки нижнего меню сделаны SVG (цвет `currentColor`), поэтому видны и у активной,
  и у неактивной кнопки. Раньше на каждой странице подключался CSS с разной версией
  (`style.css?v=2`, `?v=7`, `?v=8`), и на «Добавить» браузер брал старый файл из кэша —
  теперь один общий `vibration_isolator_base.html` и одна версия стилей.

### 5. ER-диаграмма (StarUML)
Файл `er/vibration_isolator_er.mdj` — открывается в StarUML.
Там же `vibration_isolator_er.pdf` / `.png` — готовая диаграмма на лист A4 без сетки.
- Сущности: `vibration_isolators`, `users`, `likes`; связи 1 : 0..*.
- Необязательные поля услуги (`description`, `image_url`, `video_url`) отмечены
  `nullable` (в StarUML — галочка Nullable у колонки) и подписаны в заметке на диаграмме.
- `created_at` удалён.
- Сетку в StarUML отключить: **View → Show Grid** (снять галочку).
  Печать на A4: **File → Print…** (размер бумаги A4) или **File → Export Diagram As → PNG/PDF**.

### 6. Что добавлено по ЛР-2 (методичка)
PostgreSQL в Docker, `.env` + pydantic-settings, SQLAlchemy (асинхронно, asyncpg), миграция Alembic,
поиск по названию, лайки в таблице `likes` (раньше были в localStorage браузера),
мягкое удаление через сырой SQL, сохранение новой записи со страницы «Добавить»
(раньше была только имитация через `alert`), страница 404.

---

# ЛР-3. REST API на FastAPI (по мотивам методички NestJS)

REST API для виброизоляторов: полный CRUD, фильтры, мягкое удаление, загрузка картинок в MinIO.
Работает в том же приложении и с той же БД, что и сайт из ЛР-2, под префиксом `/api`.
Новых таблиц и полей нет (в т.ч. нет `created_at`), поэтому новая миграция не нужна.

## Соответствие NestJS → FastAPI

| NestJS (методичка) | FastAPI (этот проект) |
|---|---|
| `@Entity()` `product.entity.ts` | `models/vibration_isolator.py` (SQLAlchemy) |
| `TypeORMProductsRepository` | `modules/vibration_isolator/repositories/vibration_isolator_repository.py` |
| `ProductsService` (`@Injectable`) | `modules/vibration_isolator/services/vibration_isolator_service.py` |
| `MinioSimpleService` | `modules/vibration_isolator/services/vibration_isolator_minio_service.py` |
| `ProductsController` (`@Controller`) | `modules/vibration_isolator/controllers/vibration_isolator_controller.py` (`APIRouter`) |
| `ProductsModule` (`@Module`, providers) | `modules/vibration_isolator/vibration_isolator_module.py` (`Depends`) |
| DTO + `class-validator` | `modules/vibration_isolator/dto/*.py` (Pydantic) |
| `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`) | Pydantic `extra="forbid"` + обработчик ошибок → 400 в `main.py` |
| `@Exclude()` для `isDeleted` | поля `is_deleted` просто нет в `VibrationIsolatorResponseDto` |
| `app.setGlobalPrefix('api')` | `include_router(..., prefix="/api")` |
| `ParseIntPipe` | `vibration_isolator_id: int` в пути |
| `ConfigModule` / `.env` | `core/config.py` (pydantic-settings) / `.env` |

## Маршруты

| Метод | Адрес | Что делает |
|---|---|---|
| GET | `/api/vibration_isolators` | список, фильтры: `search`, `type`, `min_stiffness`, `max_stiffness`, `min_freq`, `max_freq`, `include_deleted` |
| GET | `/api/vibration_isolators/{id}` | один виброизолятор (удалённый → 404) |
| POST | `/api/vibration_isolators` | создать (JSON), ответ 201 |
| PUT | `/api/vibration_isolators/{id}` | обновить переданные поля (удалённый → 400) |
| DELETE | `/api/vibration_isolators/{id}` | мягкое удаление (`is_deleted = true`) |
| POST | `/api/vibration_isolators/{id}/image` | загрузить картинку в MinIO (form-data, ключ `image`), старая удаляется |

Документация Swagger: http://127.0.0.1:8001/docs

## Бизнес-правила
1. Название ≥ 3 символов, тип — «Пружинный» или «Резинометаллический», жёсткость и частота > 0.
2. Лишние поля в JSON запрещены (400).
3. Удаление только мягкое; удалённые не видны в списке и по id.
4. Удалённый виброизолятор нельзя обновить и нельзя загрузить ему картинку.
5. Картинка: jpg/png/gif/webp до 5 МБ, имя файла латиницей `vibration_isolator_<id>_<время>.<расш>`,
   старая картинка из бакета `vibration-isolator` удаляется.
6. В ответе `image_url` — временная подписанная ссылка MinIO (7 дней).

## Запуск
```bash
pip install -r requirements.txt     # добавилась библиотека minio
docker-compose up -d                # PostgreSQL + Adminer
# MinIO должен быть запущен (http://localhost:9001), логин/пароль — в .env
python main.py
```
Postman: File → Import → `postman/vibration_isolator.postman_collection.json` — готовые 12 запросов.

---

# ЛР-4. Сессии и куки (FastAPI вместо NestJS)

Регистрация и вход через **куку сессии**, сессии хранятся в **Redis**, ролевая модель **user / moderator**,
заявки автоматически привязываются к автору из сессии. HTML-демо — Jinja2 (вместо Handlebars), API — в Swagger `/docs`.

## Как работает сессия
1. `POST /api/vibration_isolator_auth/login` — сервер проверяет email и пароль (хеш PBKDF2 из БД).
2. Генерирует случайный `sessionId` и пишет в Redis: `vibration_isolator_session:<sessionId> → <userId>`, TTL 1 час.
3. Отвечает заголовком `Set-Cookie: vibration_isolator_session_id=<sessionId>; HttpOnly; SameSite=lax; Max-Age=3600`.
4. Браузер / Postman сам отправляет куку в каждом запросе; «guard» находит сессию в Redis → пользователь.
5. `logout` удаляет запись из Redis — кука сразу перестаёт работать (401).

## Соответствие NestJS → FastAPI

| NestJS (методичка) | FastAPI (этот проект) |
|---|---|
| `User` / `Request` (Sequelize) | `models/user.py`, `models/vibration_isolator_request.py` (SQLAlchemy) + миграция `0002` |
| `SessionService` (ioredis) | `modules/vibration_isolator_session/vibration_isolator_session_service.py` (redis-py) |
| `UserService` | `modules/vibration_isolator_user/vibration_isolator_user_service.py` |
| `AuthService` | `modules/vibration_isolator_auth/vibration_isolator_auth_service.py` |
| `AuthController` + `res.cookie(...)` | `modules/vibration_isolator_auth/vibration_isolator_auth_controller.py` (`response.set_cookie`) |
| `SessionGuard` + `@UseGuards` | `modules/vibration_isolator_auth/vibration_isolator_session_guard.py` (`Depends`) |
| `RequestService` / `RequestController` | `modules/vibration_isolator_request/*` |
| `login.hbs`, `profile.hbs`, `AppController` | `templates/vibration_isolator_login.html`, `_register.html`, `_profile.html`, `api/vibration_isolator_auth_pages.py` |
| `cookie-parser` | встроено: `request.cookies` |
| Swagger `.addCookieAuth('sessionId')` | `APIKeyCookie` → кнопка **Authorize** в `/docs` |

## Маршруты API

| Метод | Адрес | Доступ |
|---|---|---|
| POST | `/api/vibration_isolator_auth/register` | все, ответ 201 (повтор email → 409) |
| POST | `/api/vibration_isolator_auth/login` | все, ставит куку |
| POST | `/api/vibration_isolator_auth/logout` | удаляет сессию и куку |
| GET | `/api/vibration_isolator_auth/me` | нужна кука (иначе 401) |
| POST | `/api/vibration_isolator_requests` | нужна кука; `author_id` из сессии |
| GET | `/api/vibration_isolator_requests` | user — свои, moderator — все |
| GET | `/api/vibration_isolator_requests/{id}` | своя или moderator, иначе 403 |
| PUT | `/api/vibration_isolator_requests/{id}/status` | только moderator, иначе 403 |

HTML: `/login`, `/register`, `/profile` (без куки → редирект на `/login`), кнопка «Выход».

## Учётные записи
- Модератор (создаётся миграцией из `test_user`): **moderator@vibration.ru / 123**
- Обычный пользователь — регистрируется сам (роль `user`).

## Запуск
```bash
pip install -r requirements.txt   # добавилась библиотека redis
docker-compose up -d              # + контейнер vibration_isolator_redis (порт 56379)
alembic upgrade head              # миграция 0002: поля users + таблица заявок
python main.py
```
Postman: импорт `postman/vibration_isolator_lr4.postman_collection.json` (13 запросов по порядку).
