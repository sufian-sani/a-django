from django.contrib.auth.models import Permission
from rest_framework.permissions import DjangoModelPermissions


class AuthenticatedReadDjangoModelPermissions(DjangoModelPermissions):
    read_actions = {"list", "retrieve"}

    def has_permission(self, request, view):
        if getattr(view, "action", None) in self.read_actions:
            return bool(request.user and request.user.is_authenticated)
        return super().has_permission(request, view)


def model_permission_codename(action, model_name):
    return f"{action}_{model_name.lower()}"


def model_permission_name(app_label, action, model_name):
    return f"{app_label}.{model_permission_codename(action, model_name)}"


def set_user_model_permissions(user, app_label, model_name, permission_flags):
    for action, allowed in permission_flags.items():
        if allowed is None:
            continue
        codename = model_permission_codename(action, model_name)
        try:
            permission = Permission.objects.get(
                content_type__app_label=app_label,
                codename=codename,
            )
        except Permission.DoesNotExist:
            continue

        if allowed:
            user.user_permissions.add(permission)
        else:
            user.user_permissions.remove(permission)


def user_has_model_permission(user, app_label, action, model_name):
    return user.has_perm(model_permission_name(app_label, action, model_name))
