from django.contrib.auth import get_user_model
from rest_framework import serializers

# from users.permission_utils import assign_model_permissions

# from .permissions import user_has_model_permission

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_staff",
            "is_superuser",
            "staff",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_staff",
            "is_superuser",
            "staff",
            "created_at",
            "updated_at",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "password_confirm"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        return User.objects.create_user(**validated_data)


# class AssignUserPermissionSerializer(serializers.ModelSerializer):
#     can_add_task = serializers.BooleanField(required=False)
#     can_change_task = serializers.BooleanField(required=False)
#     can_delete_task = serializers.BooleanField(required=False)
#     can_view_task = serializers.BooleanField(required=False)
#     can_add_note = serializers.BooleanField(required=False)
#     can_change_note = serializers.BooleanField(required=False)
#     can_delete_note = serializers.BooleanField(required=False)
#     can_view_note = serializers.BooleanField(required=False)

#     class Meta:
#         model = User
#         fields = [
#             "can_add_task",
#             "can_change_task",
#             "can_delete_task",
#             "can_view_task",
#             "can_add_note",
#             "can_change_note",
#             "can_delete_note",
#             "can_view_note",
#         ]

#     def update(self, instance, validated_data):
#         assign_model_permissions(instance, "task", validated_data)
#         assign_model_permissions(instance, "note", validated_data)
#         return instance


class UserDetailSerializer(serializers.ModelSerializer):
    # can_add_task = serializers.SerializerMethodField()
    # can_change_task = serializers.SerializerMethodField()
    # can_delete_task = serializers.SerializerMethodField()
    # can_view_task = serializers.SerializerMethodField()
    # can_add_note = serializers.SerializerMethodField()
    # can_change_note = serializers.SerializerMethodField()
    # can_delete_note = serializers.SerializerMethodField()
    # can_view_note = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "staff",
            "date_joined",
            "created_at",
            "updated_at",
            "groups",
            "permissions",
            # "can_add_task",
            # "can_change_task",
            # "can_delete_task",
            # "can_view_task",
            # "can_add_note",
            # "can_change_note",
            # "can_delete_note",
            # "can_view_note",
        ]

    # def get_can_add_task(self, obj):
    #     return user_has_model_permission(obj, "todo", "add", "task")

    # def get_can_change_task(self, obj):
    #     return user_has_model_permission(obj, "todo", "change", "task")

    # def get_can_delete_task(self, obj):
    #     return user_has_model_permission(obj, "todo", "delete", "task")

    # def get_can_view_task(self, obj):
    #     return user_has_model_permission(obj, "todo", "view", "task")

    # def get_can_add_note(self, obj):
    #     return user_has_model_permission(obj, "notes", "add", "note")

    # def get_can_change_note(self, obj):
    #     return user_has_model_permission(obj, "notes", "change", "note")

    # def get_can_delete_note(self, obj):
    #     return user_has_model_permission(obj, "notes", "delete", "note")

    # def get_can_view_note(self, obj):
    #     return user_has_model_permission(obj, "notes", "view", "note")
    
    def get_groups(self, obj):
        return list(obj.groups.values("id", "name"))
    
    def get_permissions(self, obj):
        perms = obj.get_all_permissions()  # set of "app.codename"

        # split codename
        codenames = [p.split(".")[1] for p in perms]

        permissions = Permission.objects.filter(codename__in=codenames)

        return [
            {
                "id": p.id,
                "name": p.name,
                "codename": p.codename,
            }
            for p in permissions
        ]


# ----------group user
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]

    def create(self, validated_data):
        permissions = validated_data.pop("permissions", [])
        group = Group.objects.create(**validated_data)
        group.permissions.set(permissions)
        return group

    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions", None)

        # instance.name = validated_data.get("name", instance.name)
        if "name" in validated_data:
            instance.name = validated_data["name"]

        instance.save()

        if permissions is not None:
            instance.permissions.set(permissions)

        return instance
    

# -----permission name
from django.contrib.auth.models import Permission
from rest_framework import serializers


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]