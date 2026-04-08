from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Task


@shared_task
def cleanup_inactive_todos():
    threshold = timezone.now() - timedelta(minutes=5)
    qs = Task.objects.filter(
        is_active=True,
        created_at__lte=threshold
    )
    for task in qs:
        task.is_active = False
        task.save()