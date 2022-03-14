"""Описание классов собственных исключений."""


class NoKeyHomeworks(Exception):
    """Исключение недоступности эндпоинта."""

    pass


class NoHomeworks(TypeError):
    """Исключение при некорректном ответе сервера."""

    pass


class NoStatusCode(Exception):
    """Исключение при некорректном статусе ответа сервера."""

    pass

