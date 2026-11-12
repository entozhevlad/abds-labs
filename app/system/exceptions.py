from typing import NoReturn


class ApiError(Exception):
    """Описывает ожидаемую ошибку API."""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(message)


def invalid(name: str, kind: str = "field") -> NoReturn:
    """Создаёт ошибку валидации поля или параметра."""
    raise ApiError(400, f'invalid "{name}" {kind}')
