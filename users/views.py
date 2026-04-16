from django.contrib.auth import authenticate, get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsStaffOrProfileStaff
from .serializers import (
    # AssignUserPermissionSerializer,
    RegisterSerializer,
    UserDetailSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if IsStaffOrProfileStaff().has_permission(self.request, self):
            return User.objects.all()
        if self.request.user.is_authenticated:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.none()

    def get_permissions(self):
        if self.action in {"create", "login", "refresh"}:
            return [permissions.AllowAny()]

        if self.action in {"list_users", "assign_permissions"}:
            return [IsStaffOrProfileStaff()]

        # if self.action == "assign_permissions":
        #     return [IsStaffOrProfileStaff()]

        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        # if self.action == "assign_permissions":
        #     return AssignUserPermissionSerializer
        if self.action in {"retrieve", "list", "list_users", "profile"}:
            return UserDetailSerializer
        if self.action == "login":
            return UserSerializer
        return RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(access),
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=["get"], url_path="list")
    def list_users(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = UserDetailSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
        )

    @action(detail=False, methods=["post"])
    def refresh(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"refresh": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
        except (InvalidToken, TokenError):
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"access": str(token.access_token)})

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        return Response(UserDetailSerializer(request.user).data)

    @action(detail=False, methods=["post"], url_path="assign-permissions")
    def assign_permissions(self, request, pk=None):
        user_ids = request.data.get("user_ids", [])
        permission_ids = request.data.get("permissions", [])

        if not user_ids:
            return Response({"error": "user_ids required"}, status=400)

        if not permission_ids:
            return Response({"error": "permissions required"}, status=400)

        users = User.objects.filter(id__in=user_ids)
        permissions = Permission.objects.filter(id__in=permission_ids)

        if not users.exists():
            return Response({"error": "No valid users found"}, status=404)

        if not permissions.exists():
            return Response({"error": "No valid permissions found"}, status=404)

        for user in users:
            user.user_permissions.add(*permissions)

        return Response({
            "message": "Permissions assigned successfully"
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"], url_path="manage-permissions", permission_classes=[IsStaffOrProfileStaff()])
    def manage_permissions(self, request):
        user_ids = request.data.get("user_ids", [])
        add_ids = request.data.get("add_permissions", [])
        remove_ids = request.data.get("remove_permissions", [])

        if not user_ids:
            return Response({"error": "user_ids required"}, status=400)

        users = User.objects.filter(id__in=user_ids)

        add_perms = Permission.objects.filter(id__in=add_ids)
        remove_perms = Permission.objects.filter(id__in=remove_ids)

        for user in users:
            if add_perms:
                user.user_permissions.add(*add_perms)

            if remove_perms:
                user.user_permissions.remove(*remove_perms)

        return Response({
            "message": "Permissions updated successfully"
        })
    
    @action(detail=False, methods=["post"], url_path="add-to-group", permission_classes=[IsStaffOrProfileStaff()])
    def add_to_group(self, request):
        user_ids = request.data.get("user_ids", [])
        group_ids = request.data.get("groups", [])

        if not user_ids:
            return Response({"error": "user_ids is required"}, status=400)

        if not group_ids:
            return Response({"error": "groups is required"}, status=400)

        users = User.objects.filter(id__in=user_ids)
        groups = Group.objects.filter(id__in=group_ids)

        for user in users:
            user.groups.add(*groups)

        return Response({
            "message": "Users added to groups successfully"
    }, status=status.HTTP_200_OK)


# -----group api
from django.contrib.auth.models import Group
from rest_framework import viewsets, permissions
from .serializers import GroupSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsStaffOrProfileStaff]


# -----permission name
from django.contrib.auth.models import Permission
from rest_framework import viewsets, permissions
from django.apps import apps

from .serializers import (
    PermissionSerializer
)



class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsStaffOrProfileStaff]

    def get_queryset(self):
        allowed_apps = ["todo", "users", "notes"]  # your apps only

        return Permission.objects.filter(
            content_type__app_label__in=allowed_apps
        )