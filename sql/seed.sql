-- Начальные данные. Выполнить в Adminer → «SQL-команда» после `alembic upgrade head`.

-- Тестовый пользователь (его id = 1 используется для лайков)
INSERT INTO users (id, username) VALUES (1, 'test_user');

-- Виброизоляторы (фото/видео лежат в MinIO, бакет media: http://localhost:9000/media/)
INSERT INTO vibration_isolators (id, title, type, stiffness, freq, description, image_url, video_url, is_deleted) VALUES
  (1, 'Пружинный АР-120', 'Пружинный', 45, 4.2,
   'Пружинный виброизолятор для насосов и вентиляторов. Обеспечивает снижение вибрации до 85%. Рекомендуемая нагрузка до 120 кг. Идеален для оборудования с частотой вращения до 1500 об/мин.',
   'http://localhost:9000/media/vibro1.png', 'http://localhost:9000/media/vibro1.mp4', false),
  (2, 'Резинометаллический РМ-80', 'Резинометаллический', 32, 6.8,
   'Резинометаллический виброизолятор для вентиляционных установок. Высокая демпфирующая способность. Нагрузка до 80 кг. Эффективен при средних частотах.',
   'http://localhost:9000/media/vibro2.png', 'http://localhost:9000/media/vibro2.mp4', false),
  (3, 'Пружинный ПВ-200', 'Пружинный', 78, 3.1,
   'Мощный пружинный виброизолятор для тяжелого оборудования. Нагрузка до 200 кг. Низкая собственная частота — отличная изоляция на низких частотах.',
   'http://localhost:9000/media/vibro3.png', 'http://localhost:9000/media/vibro3.mp4', false),
  (4, 'Резинометаллический РМ-150', 'Резинометаллический', 55, 5.0,
   'Универсальный резинометаллический виброизолятор. Нагрузка до 150 кг. Применяется для компрессоров и насосов. Снижение вибрации до 80%.',
   'http://localhost:9000/media/vibro4.png', 'http://localhost:9000/media/vibro4.mp4', false),
  (5, 'Пружинный АР-90', 'Пружинный', 28, 7.5,
   'Компактный пружинный виброизолятор для малогабаритного оборудования. Нагрузка до 90 кг. Отличное решение для вентиляторов малой мощности.',
   'http://localhost:9000/media/vibro5.png', 'http://localhost:9000/media/vibro5.mp4', false);

-- Сдвигаем счётчик id, чтобы новые записи со страницы «Добавить» получали id = 6, 7, ...
SELECT setval('vibration_isolators_id_seq', (SELECT MAX(id) FROM vibration_isolators));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
