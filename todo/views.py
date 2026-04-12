from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from .forms import TaskForm
from .models import Task


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "todo/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = TaskForm()
        return context


class TaskCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "todo.add_task"
    raise_exception = True

    def post(self, request, *args, **kwargs):
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
        return redirect("task_list")


class TaskToggleView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "todo.change_task"
    raise_exception = True

    def post(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, id=task_id, owner=request.user)
        task.completed = not task.completed
        task.save(update_fields=["completed"])
        return redirect("task_list")


class TaskDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "todo.delete_task"
    raise_exception = True

    def post(self, request, task_id, *args, **kwargs):
        task = get_object_or_404(Task, id=task_id, owner=request.user)
        task.delete()
        return redirect("task_list")
