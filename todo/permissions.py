from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated

class TaskPermission(DjangoModelPermissions):
    def has_permission(self, request, view):
        # list/retrieve فقط login user
        if view.action in ["list", "retrieve"]:
            return bool(request.user and request.user.is_authenticated)

        # create/update/delete -> use Django model permissions
        return super().has_permission(request, view)