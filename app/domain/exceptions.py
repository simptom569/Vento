class DomainError(Exception):
    """Базовый класс для всех доменных исключений"""
    pass


class NotFoundError(DomainError):
    """Сущность не найдена"""
    pass


class AlreadyExistsError(DomainError):
    """Сущность уже существует"""
    pass


class ForbiddenError(DomainError):
    """Нет прав на действие"""
    pass


class ValidationError(DomainError):
    """Бизнес-валидация не прошла"""
    pass


class TokenTheftError(DomainError):
    """Повторное использование refresh токена"""
    pass