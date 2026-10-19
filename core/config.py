"""
Настройки приложения.

Параметры подключения к БД не пишутся прямо в коде, а читаются из файла .env
с помощью pydantic-settings. Если какой-то переменной нет — приложение
сразу упадёт с понятной ошибкой (поля обязательные и типизированные).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str          # адрес сервера PostgreSQL (localhost)
    DB_PORT: int          # порт (5432)
    DB_USER: str          # пользователь БД
    DB_PASSWORD: str      # пароль
    DB_NAME: str          # имя базы: vibration_isolator_db

    # Откуда читать переменные окружения
    model_config = SettingsConfigDict(env_file=".env")

    @property
    def DATABASE_URL(self) -> str:
        # Строка подключения для асинхронного драйвера asyncpg
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


# Единственный объект настроек, импортируется во всём проекте
settings = Settings()
