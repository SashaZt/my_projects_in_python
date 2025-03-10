# app/core/exceptions.py
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Исключение для случаев, когда ресурс не найден."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DatabaseError(HTTPException):
    """Исключение для ошибок базы данных."""
    
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class ValidationError(HTTPException):
    """Исключение для ошибок валидации данных."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class AuthenticationError(HTTPException):
    """Исключение для ошибок аутентификации."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )