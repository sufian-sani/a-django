from django.contrib.auth.models import Permission
from rest_framework.permissions import BasePermission, DjangoModelPermissions


class AuthenticatedReadDjangoModelPermissions(DjangoModelPermissions):
    authenticated_only_actions = {"list"}

    def has_permission(self, request, view):
        if getattr(view, "action", None) in self.authenticated_only_actions:
            return bool(request.user and request.user.is_authenticated)
        return super().has_permission(request, view)

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


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


class IsStaffOrProfileStaff(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(user.is_staff or getattr(user, "staff", False))


class AppModelPermissions(AuthenticatedReadDjangoModelPermissions):
    app_label = None
    model_name = None

    def has_permission(self, request, view):
        if self.app_label and self.model_name:
            view.required_permission_app = self.app_label
            view.required_permission_model = self.model_name
        return super().has_permission(request, view)

    def _queryset(self, view):
        queryset = getattr(view, "queryset", None)
        if queryset is not None:
            return queryset

        app_label = getattr(view, "required_permission_app", None) or self.app_label
        model_name = getattr(view, "required_permission_model", None) or self.model_name
        if not app_label or not model_name:
            return super()._queryset(view)

        meta = type("Meta", (), {"app_label": app_label, "model_name": model_name})
        model = type("Model", (), {"_meta": meta()})
        queryset_type = type("QuerySet", (), {"model": model()})
        return queryset_type()


def build_app_model_permission(app_label, model_name):
    class GeneratedAppModelPermission(AppModelPermissions):
        pass

    GeneratedAppModelPermission.app_label = app_label
    GeneratedAppModelPermission.model_name = model_name
    GeneratedAppModelPermission.__name__ = f"{app_label.title()}{model_name.title()}Permission"
    return GeneratedAppModelPermission
