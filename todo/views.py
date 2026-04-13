from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Task
from .permissions import TaskPermission
from .serializers import TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    # 1. REQUIRED: DRF needs this to know it's checking 'task.add_task'
    queryset = Task.objects.all() 
    
    serializer_class = TaskSerializer
    
    # 2. Use your custom class (or standard DjangoModelPermissions)
    permission_classes = [TaskPermission] 

    def get_queryset(self):
        # 3. Filter the base queryset so users only see their own tasks
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # 4. Automatically set the owner during creation
        serializer.save(owner=self.request.user)
