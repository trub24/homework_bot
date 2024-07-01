class RequestError(Exception):
    """Класс ошибок обрабатывающий ошибки: недоступность сервера."""

    pass


class UnexpectedStatusErorr(Exception):
    """Класс ошибок обрабатывающий ошибки отправки сообщения."""

    pass
