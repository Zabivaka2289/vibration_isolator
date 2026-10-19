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
```

## Структура проекта

```text
vibration_isolator/
├── alembic/
│   ├── versions/0001_init_vibration_isolators_users_likes.py  — миграция: 3 таблицы
│   ├── env.py                — Alembic берёт адрес БД из .env и модели из models/
│   └── script.py.mako        — шаблон новых миграций
├── alembic.ini               — настройки Alembic
├── api/handlers.py           — все страницы и действия (роуты)
├── core/config.py            — чтение .env через pydantic-settings
├── db/base.py                — базовый класс моделей
├── db/session.py             — подключение к БД, сессия на каждый запрос
├── models/
│   ├── vibration_isolator.py — модель VibrationIsolator (таблица vibration_isolators)
│   ├── user.py               — модель User (таблица users)
│   └── like.py               — модель Like (таблица likes)
├── templates/
│   ├── base.html             — общий каркас: «телефон» 390×844 + нижнее меню
│   ├── _card.html            — карточка для Плитки и Фильтра
│   ├── index.html            — Плитка + поиск
│   ├── filter.html           — фильтр по жёсткости
│   ├── vibration_isolator.html — Лента (одна карточка на экран)
│   ├── add.html              — Добавить (сохранение в БД)
│   └── 404.html              — «не найдено»
├── static/
│   ├── css/style.css
│   ├── img/                  — иконки и заглушки «нет фото / нет видео»
│   └── media/                — фото и видео виброизоляторов vibration_isolator_N.png/.mp4
├── sql/seed.sql              — начальные данные
├── er/                       — ER-диаграмма (StarUML .mdj + PDF/PNG под A4)
├── docker-compose.yml
├── .env / .env.example
├── .gitignore
├── main.py
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
- шаблон Ленты `templates/vibration_isolator.html` (был `hotel.html`);
- адреса `/vibration_isolator/{id}`, `/vibration_isolator/{id}/like`, `/vibration_isolator/{id}/delete`
  (было `/isolator/{id}`);
- переменные в коде и шаблонах: `vibration_isolators`, `vibration_isolator_id`;
- БД `vibration_isolator_db`, пользователь `vibration_isolator_user`, контейнеры
  `vibration_isolator_postgres` / `vibration_isolator_adminer`, том `vibration_isolator_pgdata`;
- медиафайлы `static/media/vibration_isolator_1.png … _5.png` (были `vibro1.png …`);
- cookie последней карточки `last_vibration_isolator_id`.

### 2. Фиксированный размер телефона, без адаптивности
Раньше страница растягивалась на весь экран (`width: 100vw; height: 100vh`) и были `@media`-правила.
Теперь всё содержимое лежит в блоке `.phone` фиксированного размера **390 × 844 px**
(`templates/base.html`, `static/css/style.css`). Все `@media` удалены, нижнее меню и шапки
позиционируются внутри «телефона», а не по окну браузера. Размер меняется в одном месте —
переменные `--phone-w` / `--phone-h` в начале `style.css`.

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
  теперь один общий `base.html` и одна версия стилей.

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
