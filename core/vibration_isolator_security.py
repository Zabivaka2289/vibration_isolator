"""
vibration_isolator: хеширование паролей.

В методичке NestJS пароль хранится открытым текстом — так делать нельзя,
поэтому здесь пароль хешируется алгоритмом PBKDF2-SHA256 со случайной солью
(встроенный модуль hashlib, дополнительные библиотеки не нужны).
Формат в БД:  pbkdf2_sha256$<итерации>$<соль>$<хеш>
"""
import hashlib
import secrets

VIBRATION_ISOLATOR_PBKDF2_ITERATIONS = 200_000


def vibration_isolator_hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(),
                                 VIBRATION_ISOLATOR_PBKDF2_ITERATIONS).hex()
    return f"pbkdf2_sha256${VIBRATION_ISOLATOR_PBKDF2_ITERATIONS}${salt}${digest}"


def vibration_isolator_verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, digest = stored.split("$")
    except (ValueError, AttributeError):
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    # compare_digest — сравнение за постоянное время (защита от атак по времени)
    return secrets.compare_digest(check, digest)
