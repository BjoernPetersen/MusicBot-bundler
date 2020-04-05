class StatusCodeException(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(f'{message}')
        self.code = code


class BadRequestException(StatusCodeException):
    def __init__(self, message=""):
        super().__init__(400, message)


class ForbiddenException(StatusCodeException):
    def __init__(self, message=""):
        super().__init__(403, message)


class NotFoundException(StatusCodeException):
    def __init__(self, message=""):
        super().__init__(404, message)
