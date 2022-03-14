"""Описание классов собственных исключений."""


class NoKeyHomeworks(Exception):
    """Исключение при отсутсвии ключа дз."""

    pass


class NoHomeworks(TypeError):
    """Исключение при отсутсвии дз."""

    pass


class NoStatusCode(Exception):
    """Исключение при неверном статусе дз."""

    pass

