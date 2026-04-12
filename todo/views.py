from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user)
    form = TaskForm()
    return render(request, "todo/task_list.html", {"tasks": tasks, "form": form})


@login_required
@permission_required("todo.add_task", raise_exception=True)
@require_POST
def create_task(request):
    form = TaskForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
    return redirect("task_list")


@login_required
@permission_required("todo.change_task", raise_exception=True)
@require_POST
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.completed = not task.completed
    task.save(update_fields=["completed"])
    return redirect("task_list")


@login_required
@permission_required("todo.delete_task", raise_exception=True)
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.delete()
    return redirect("task_list")
