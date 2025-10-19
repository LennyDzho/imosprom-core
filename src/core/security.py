import hashlib
import secrets
import base64


def get_password_hash(password: str) -> str:
    """Хэширование пароля с солью"""
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Количество итераций
    )
    # Сохраняем соль и хэш вместе
    return base64.b64encode(salt + key).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        decoded = base64.b64decode(hashed_password)
        salt = decoded[:32]
        stored_key = decoded[32:]

        computed_key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            100000
        )

        return secrets.compare_digest(computed_key, stored_key)
    except Exception:
        return False