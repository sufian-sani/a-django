from rest_framework import viewsets

from .models import Task
from .permissions import DjangoModelPermissionsWithView
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [DjangoModelPermissionsWithView]

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
