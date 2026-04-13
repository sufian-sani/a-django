from users.permissions import AppModelPermissions


class TaskPermission(AppModelPermissions):
    app_label = "todo"
    model_name = "task"
