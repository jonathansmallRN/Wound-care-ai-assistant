class ErrorCode:
    AI_UNAVAILABLE = "AI_UNAVAILABLE"
    AI_LOW_CONFIDENCE = "AI_LOW_CONFIDENCE"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    OVERRIDE_INCOMPLETE = "OVERRIDE_INCOMPLETE"
    NOT_FOUND = "NOT_FOUND"


class AppError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(404, ErrorCode.NOT_FOUND, message)


class ValidationFailedError(AppError):
    def __init__(self, message: str):
        super().__init__(422, ErrorCode.VALIDATION_ERROR, message)
