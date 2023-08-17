class PermissionDenied(Exception):
    def __init__(self, message='Permission denied'):
        self.message = message
        super().__init__(self.message)


class SerializerValidationError(Exception):
    def __init__(self, field: str, message='- no such field exists'):
        self.message = field + message
        super().__init__(self.message)
