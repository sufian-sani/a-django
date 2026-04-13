from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .permission_registry import PERMISSION_REGISTRY
from .permissions import build_app_model_permission


def assign_model_permissions(user, config_key, validated_data):
    config = PERMISSION_REGISTRY[config_key]

    app_label = config["app_label"]
    model_name = config["model_name"]
    fields = config["fields"]

    content_type = ContentType.objects.get(
        app_label=app_label,
        model=model_name,
    )

    for action, field_name in fields.items():
        allowed = validated_data.get(field_name, None)

        if allowed is None:
            continue

        codename = f"{action}_{model_name}"

        try:
            permission = Permission.objects.get(
                codename=codename,
                content_type=content_type,
            )
        except Permission.DoesNotExist:
            continue

        if allowed:
            user.user_permissions.add(permission)
        else:
            user.user_permissions.remove(permission)


def permission_class_from_registry(config_key):
    config = PERMISSION_REGISTRY[config_key]
    return build_app_model_permission(
        app_label=config["app_label"],
        model_name=config["model_name"],
    )
