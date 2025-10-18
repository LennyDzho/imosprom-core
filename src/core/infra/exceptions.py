from logging import Logger
from typing import Optional, Any


class AppException(Exception):

    detail: Optional[str]
    code: Optional[str]
    extra: dict

    def __init__(
        self, detail: Optional[str] = None, code: Optional[str] = None, **extra: Any
    ):
        self.detail = detail
        self.code = code
        self.extra = extra
        super().__init__(detail)

    def __str__(self) -> str:
        code_part = f" [{self.code}]" if self.code else ""
        extra_part = f" | {self.extra}" if self.extra else ""
        return f"{self.__class__.__name__}: {self.detail or ''}{code_part}{extra_part}"

    def log(self, logger: Logger) -> None:
        logger.error(str(self))


class NotApiKey(AppException):
    """Требуется авторизация"""


class InvalidApiKey(AppException):
    """Неверный API ключ"""


class Forbidden(AppException):
    """Доступ запрещён"""


class NotFound(AppException):
    """Запись не найдена"""


class InactiveUser(AppException):
    """Пользователь не активен"""


class Conflict(AppException):
    """Конфликт данных"""

class AppException(Exception):
    """Базовое исключение приложения"""
    pass

class UserAlreadyExists(AppException):
    def __init__(self, message="Пользователь с таким email уже существует"):
        self.message = message
        super().__init__(self.message)

class InvalidCredentials(AppException):
    def __init__(self, message="Неверные учетные данные"):
        self.message = message
        super().__init__(self.message)

class InvalidToken(AppException):
    def __init__(self, message="Невалидный токен"):
        self.message = message
        super().__init__(self.message)

class UserNotFound(AppException):
    def __init__(self, message="Пользователь не найден"):
        self.message = message
        super().__init__(self.message)