from users.permissions import AuthenticatedReadDjangoModelPermissions


class TaskPermission(AuthenticatedReadDjangoModelPermissions):
    pass
