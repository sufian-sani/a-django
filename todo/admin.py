from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "completed", "is_active", "created_at", "updated_at")
    list_filter = ("completed", "is_active", "created_at")
    search_fields = ("title",)
