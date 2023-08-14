class PermissionAdmin:
    @staticmethod
    def permission(object) -> bool:
        return object.is_admin
