from django.contrib.auth.models import User
from rest_framework import serializers

from users.permission_utils import assign_model_permissions

from .permissions import set_user_model_permissions, user_has_model_permission
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["id", "staff", "created_at", "updated_at"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff", "is_superuser", "profile"]
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

    can_add_note = serializers.BooleanField(required=False)
    can_change_note = serializers.BooleanField(required=False)
    can_delete_note = serializers.BooleanField(required=False)
    can_view_note = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            "can_add_task",
            "can_change_task",
            "can_delete_task",
            "can_view_task",
            "can_add_note",
            "can_change_note",
            "can_delete_note",
            "can_view_note",
        ]

    def update(self, instance, validated_data):
        assign_model_permissions(instance, "task", validated_data)
        assign_model_permissions(instance, "note", validated_data)
        return instance
    

class UserDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    can_add_task = serializers.SerializerMethodField()
    can_change_task = serializers.SerializerMethodField()
    can_delete_task = serializers.SerializerMethodField()
    can_view_task = serializers.SerializerMethodField()

    can_add_note = serializers.SerializerMethodField()
    can_change_note = serializers.SerializerMethodField()
    can_delete_note = serializers.SerializerMethodField()
    can_view_note = serializers.SerializerMethodField()

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
            "profile",
            "can_add_task",
            "can_change_task",
            "can_delete_task",
            "can_view_task",
            "can_add_note",
            "can_change_note",
            "can_delete_note",
            "can_view_note",
        ]

    def get_can_add_task(self, obj):
        return user_has_model_permission(obj, "todo", "add", "task")

    def get_can_change_task(self, obj):
        return user_has_model_permission(obj, "todo", "change", "task")

    def get_can_delete_task(self, obj):
        return user_has_model_permission(obj, "todo", "delete", "task")

    def get_can_view_task(self, obj):
        return user_has_model_permission(obj, "todo", "view", "task")
    
    def get_can_add_note(self, obj):
        return user_has_model_permission(obj, "notes", "add", "note")
    
    def get_can_change_note(self, obj):
        return user_has_model_permission(obj, "notes", "change", "note")
    
    def get_can_delete_note(self, obj):
        return user_has_model_permission(obj, "notes", "delete", "note")
    
    def get_can_view_note(self, obj):
        return user_has_model_permission(obj, "notes", "view", "note")
