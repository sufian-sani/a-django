from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("groups", views.GroupViewSet, basename="groups")
router.register("permissions", views.PermissionViewSet, basename="permissions")
router.register("", views.UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
