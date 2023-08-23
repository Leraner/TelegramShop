class PermissionDenied(Exception):
    """Exception if user hasn't enough privileges to do something"""
    def __init__(self, message='Permission denied') -> None:
        self.message = message
        super().__init__(self.message)


class SerializerValidationError(Exception):
    """Exception for validation error, if no such field exists or validation error"""
    def __init__(self, field: str = '', message='- no such field exists') -> None:
        self.message = field + message
        super().__init__(self.message)
