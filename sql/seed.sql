-- Начальные данные. Выполнить в Adminer → «SQL-команда» после `alembic upgrade head`.

-- Тестовый пользователь (его id = 1 используется для лайков)
INSERT INTO users (id, username) VALUES (1, 'test_user');

-- Виброизоляторы (картинки/видео лежат в static/media/)
INSERT INTO vibration_isolators (id, title, type, stiffness, freq, description, image_url, video_url, is_deleted) VALUES
  (1, 'Пружинный АР-120', 'Пружинный', 45, 4.2,
   'Пружинный виброизолятор для насосов и вентиляторов. Обеспечивает снижение вибрации до 85%. Рекомендуемая нагрузка до 120 кг. Идеален для оборудования с частотой вращения до 1500 об/мин.',
   '/static/media/vibration_isolator_1.png', '/static/media/vibration_isolator_1.mp4', false),
  (2, 'Резинометаллический РМ-80', 'Резинометаллический', 32, 6.8,
   'Резинометаллический виброизолятор для вентиляционных установок. Высокая демпфирующая способность. Нагрузка до 80 кг. Эффективен при средних частотах.',
   '/static/media/vibration_isolator_2.png', '/static/media/vibration_isolator_2.mp4', false),
  (3, 'Пружинный ПВ-200', 'Пружинный', 78, 3.1,
   'Мощный пружинный виброизолятор для тяжелого оборудования. Нагрузка до 200 кг. Низкая собственная частота — отличная изоляция на низких частотах.',
   '/static/media/vibration_isolator_3.png', '/static/media/vibration_isolator_3.mp4', false),
  (4, 'Резинометаллический РМ-150', 'Резинометаллический', 55, 5.0,
   'Универсальный резинометаллический виброизолятор. Нагрузка до 150 кг. Применяется для компрессоров и насосов. Снижение вибрации до 80%.',
   '/static/media/vibration_isolator_4.png', '/static/media/vibration_isolator_4.mp4', false),
  (5, 'Пружинный АР-90', 'Пружинный', 28, 7.5,
   'Компактный пружинный виброизолятор для малогабаритного оборудования. Нагрузка до 90 кг. Отличное решение для вентиляторов малой мощности.',
   '/static/media/vibration_isolator_5.png', '/static/media/vibration_isolator_5.mp4', false);

-- Сдвигаем счётчик id, чтобы новые записи со страницы «Добавить» получали id = 6, 7, ...
SELECT setval('vibration_isolators_id_seq', (SELECT MAX(id) FROM vibration_isolators));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
