"""Описание классов собственных исключений."""


class NoKeyHomeworksCurrentDateError(Exception):
    """Исключение при отсутсвии ключа дз."""

    pass


class EmptyResponseError(TypeError):
    """Исключение при отсутсвии дз."""

    pass


class NoStatusCodeError(Exception):
    """Исключение при неверном статусе дз."""

    pass

