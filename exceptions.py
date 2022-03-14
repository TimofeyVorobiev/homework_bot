"""Описание классов собственных исключений."""


class EndpointError(Exception):
    """Исключение недоступности эндпоинта."""

    pass


class InvalidResponse(TypeError):
    """Исключение при некорректном ответе сервера."""

    pass


class NoStatusCode(Exception):
    """Исключение при некорректном статусе ответа сервера."""

    pass


class KeyNotFind(KeyError):
    """Исключение при отсутствии ключа для словаря."""

    pass


class VariableNotDefined(Exception):
    """Исключение при незаданности переменных окружения."""

    pass
