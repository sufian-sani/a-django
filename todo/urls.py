from django.urls import path

from . import views


urlpatterns = [
    path("", views.TaskListView.as_view(), name="task_list"),
    path("create/", views.TaskCreateView.as_view(), name="create_task"),
    path("toggle/<int:task_id>/", views.TaskToggleView.as_view(), name="toggle_task"),
    path("delete/<int:task_id>/", views.TaskDeleteView.as_view(), name="delete_task"),
]
