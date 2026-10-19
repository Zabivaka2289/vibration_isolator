"""
Настройки приложения vibration_isolator.

Параметры подключения к БД и MinIO не пишутся прямо в коде, а читаются из файла .env
с помощью pydantic-settings (аналог ConfigModule + ConfigService в NestJS).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- vibration_isolator: PostgreSQL (ЛР-2) ----
    DB_HOST: str          # адрес сервера PostgreSQL
    DB_PORT: int          # порт на компьютере (55432)
    DB_USER: str          # пользователь БД
    DB_PASSWORD: str      # пароль
    DB_NAME: str          # имя базы: vibration_isolator_db

    # ---- vibration_isolator: MinIO (ЛР-3) ----
    # Значения по умолчанию подходят для стандартного MinIO на localhost:9000
    MINIO_ENDPOINT: str = "localhost:9000"        # адрес API MinIO (не консоли 9001!)
    MINIO_ACCESS_KEY: str = "minioadmin"          # логин MinIO
    MINIO_SECRET_KEY: str = "minioadmin"          # пароль MinIO
    MINIO_BUCKET: str = "vibration-isolator"      # бакет для картинок (в имени бакета нельзя «_»)
    MINIO_USE_SSL: bool = False

    # ---- vibration_isolator: Redis для сессий (ЛР-4) ----
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 56379                       # необычный порт, чтобы не мешать другим Redis
    VIBRATION_ISOLATOR_SESSION_TTL: int = 3600    # время жизни сессии, секунд (1 час)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        # Строка подключения для асинхронного драйвера asyncpg
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def MINIO_PUBLIC_URL(self) -> str:
        # Базовый адрес файлов в MinIO, например http://localhost:9000
        protocol = "https" if self.MINIO_USE_SSL else "http"
        return f"{protocol}://{self.MINIO_ENDPOINT}"


# Единственный объект настроек, импортируется во всём проекте
settings = Settings()
