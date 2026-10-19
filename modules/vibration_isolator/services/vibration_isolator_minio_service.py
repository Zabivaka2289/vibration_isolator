"""
vibration_isolator: сервис MinIO — аналог MinioSimpleService в NestJS.

MinIO — S3-совместимое объектное хранилище. Схема работы:
  1) файл → MinIO → получаем адрес файла;
  2) адрес сохраняем в БД (vibration_isolators.image_url);
  3) при выдаче клиенту генерируем временную подписанную ссылку (presigned URL, 7 дней).

Клиент MinIO синхронный, поэтому вызовы оборачиваются в run_in_threadpool,
чтобы не блокировать асинхронный сервер.
"""
import io
import json
import time
from datetime import timedelta
from urllib.parse import urlparse

from minio import Minio
from starlette.concurrency import run_in_threadpool

from core.config import settings

# Расширение файла по MIME-типу. Имя файла всегда латиницей.
VIBRATION_ISOLATOR_IMAGE_EXT = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}


class VibrationIsolatorMinioService:
    def __init__(self):
        self.bucket = settings.MINIO_BUCKET
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self._bucket_ready = False

    # ------------------------------------------------------------------
    def _ensure_bucket(self) -> None:
        """Создаёт бакет при первом обращении и открывает его на чтение
        (чтобы картинки показывались и на HTML-страницах из ЛР-2)."""
        if self._bucket_ready:
            return
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            print(f'vibration_isolator: бакет "{self.bucket}" создан в MinIO')
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{self.bucket}/*"],
            }],
        }
        self.client.set_bucket_policy(self.bucket, json.dumps(policy))
        self._bucket_ready = True

    def _split_url(self, url: str) -> tuple[str, str] | None:
        """http://localhost:9000/<бакет>/<файл> → (бакет, файл).
        Если ссылка не на наш MinIO — None."""
        if not url or not url.startswith(settings.MINIO_PUBLIC_URL + "/"):
            return None
        path = urlparse(url).path.lstrip("/")
        if "/" not in path:
            return None
        bucket, object_name = path.split("/", 1)
        return bucket, object_name

    # ------------------------------------------------------------------
    async def upload_vibration_isolator_image(
        self, data: bytes, vibration_isolator_id: int, content_type: str
    ) -> str:
        """Загружает картинку и возвращает её постоянный адрес для БД."""
        ext = VIBRATION_ISOLATOR_IMAGE_EXT.get(content_type, "jpg")
        file_name = f"vibration_isolator_{vibration_isolator_id}_{int(time.time() * 1000)}.{ext}"

        def _upload():
            self._ensure_bucket()
            self.client.put_object(
                self.bucket, file_name, io.BytesIO(data), length=len(data),
                content_type=content_type,
            )

        await run_in_threadpool(_upload)
        return f"{settings.MINIO_PUBLIC_URL}/{self.bucket}/{file_name}"

    async def get_signed_url(self, url: str | None) -> str | None:
        """Временная подписанная ссылка на 7 дней. Для чужих ссылок — сама ссылка."""
        if not url:
            return None
        parts = self._split_url(url)
        if parts is None:
            return url
        bucket, object_name = parts
        try:
            return await run_in_threadpool(
                self.client.presigned_get_object, bucket, object_name, timedelta(days=7)
            )
        except Exception as error:  # MinIO недоступен — отдаём обычную ссылку
            print("vibration_isolator: не удалось подписать ссылку:", error)
            return url

    async def delete_file(self, url: str) -> None:
        """Удаляет файл, но только из СВОЕГО бакета
        (исходные фото в бакете media не трогаем)."""
        parts = self._split_url(url)
        if parts is None or parts[0] != self.bucket:
            return
        try:
            await run_in_threadpool(self.client.remove_object, parts[0], parts[1])
        except Exception as error:
            print("vibration_isolator: не удалось удалить старую картинку:", error)
