class PermissionDenied(Exception):
    def __init__(self, message='Permission denied'):
        self.message = message
        super().__init__(self.message)
