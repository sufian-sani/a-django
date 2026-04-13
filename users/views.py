from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import AssignUserPermissionSerializer, RegisterSerializer, UserDetailSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return User.objects.all()
        return User.objects.none()

    def get_permissions(self):
        if self.action in {"create", "login", "refresh"}:
            return [permissions.AllowAny()]

        if self.action == "profile":
            return [permissions.IsAuthenticated()]

        if self.action == "assign_permissions":
            return [permissions.IsAdminUser()]   # staff only

        return [permissions.IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == "assign_permissions":
            return AssignUserPermissionSerializer
        if self.action in {"retrieve", "list"}:
            return UserDetailSerializer
        return RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        headers = self.get_success_headers(serializer.data)
        return Response({
            "user": serializer.data,
            "refresh": str(refresh),
            "access": str(access),
        }, status=status.HTTP_201_CREATED, headers=headers)

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

        return Response(
            {
                "access": str(token.access_token),
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        return Response(UserDetailSerializer(request.user).data)
    

    @action(detail=True, methods=["patch"], url_path="assign-permissions")
    def assign_permissions(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Permissions updated successfully.",
            "user_id": user.id,
            "username": user.username,
        }, status=status.HTTP_200_OK)
