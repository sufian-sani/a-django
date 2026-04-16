from users.permissions import AppModelPermissions


class TaskPermission(AppModelPermissions):
    app_label = "todo"
    model_name = "task"

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
