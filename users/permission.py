from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from todo.models import Task

# create a role
manager_group, _ = Group.objects.get_or_create(name="Project Manager")

# get model permissions
permissions = Permission.objects.filter(
    content_type=ContentType.objects.get_for_model(Task),
    codename__in=[
        "add_task",
        "change_task",
        "delete_task",
        "view_task",
    ]
)

manager_group.permissions.set(permissions)