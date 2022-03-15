"""Описание классов собственных исключений."""


class BotSendMessageError(TypeError):
    """Исключение при отсутсвии дз."""

    pass


class StatusCodeError(Exception):
    """Исключение при неверном статусе дз."""

    pass

