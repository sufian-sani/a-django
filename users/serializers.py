from django.contrib.auth.models import Permission, User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_superuser"]
        read_only_fields = ["id", "is_staff", "is_superuser"]


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
    

class AssignUserPermissionSerializer(serializers.ModelSerializer):
    can_add_task = serializers.BooleanField(required=False)
    can_change_task = serializers.BooleanField(required=False)
    can_delete_task = serializers.BooleanField(required=False)
    can_view_task = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            "can_add_task",
            "can_change_task",
            "can_delete_task",
            "can_view_task",
        ]

    def update(self, instance, validated_data):
        permission_map = {
            "add_task": validated_data.get("can_add_task", None),
            "change_task": validated_data.get("can_change_task", None),
            "delete_task": validated_data.get("can_delete_task", None),
            "view_task": validated_data.get("can_view_task", None),
        }

        for codename, allowed in permission_map.items():
            if allowed is None:
                continue

            try:
                permission = Permission.objects.get(codename=codename)
            except Permission.DoesNotExist:
                continue

            if allowed:
                instance.user_permissions.add(permission)
            else:
                instance.user_permissions.remove(permission)

        return instance
    

class UserDetailSerializer(serializers.ModelSerializer):
    can_add_task = serializers.SerializerMethodField()
    can_change_task = serializers.SerializerMethodField()
    can_delete_task = serializers.SerializerMethodField()
    can_view_task = serializers.SerializerMethodField()

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
            "date_joined",
            "can_add_task",
            "can_change_task",
            "can_delete_task",
            "can_view_task",
        ]

    def get_can_add_task(self, obj):
        return obj.has_perm("todo.add_task")

    def get_can_change_task(self, obj):
        return obj.has_perm("todo.change_task")

    def get_can_delete_task(self, obj):
        return obj.has_perm("todo.delete_task")

    def get_can_view_task(self, obj):
        return obj.has_perm("todo.view_task")
