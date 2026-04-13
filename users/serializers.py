from django.contrib.auth.models import User
from rest_framework import serializers

from .permissions import set_user_model_permissions, user_has_model_permission


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
        set_user_model_permissions(
            user=instance,
            app_label="todo",
            model_name="task",
            permission_flags={
                "add": validated_data.get("can_add_task", None),
                "change": validated_data.get("can_change_task", None),
                "delete": validated_data.get("can_delete_task", None),
                "view": validated_data.get("can_view_task", None),
            },
        )

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
        return user_has_model_permission(obj, "todo", "add", "task")

    def get_can_change_task(self, obj):
        return user_has_model_permission(obj, "todo", "change", "task")

    def get_can_delete_task(self, obj):
        return user_has_model_permission(obj, "todo", "delete", "task")

    def get_can_view_task(self, obj):
        return user_has_model_permission(obj, "todo", "view", "task")
