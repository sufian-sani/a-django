from django.db import models
from django.conf import settings

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Theme(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

def get_default_theme():
    # Returns the primary key of the default theme, creating it if necessary
    theme, _ = Theme.objects.get_or_create(name="Standard")
    return theme.id

class Reviewer(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

def get_fallback_reviewer():
    # SET() accepts a callable or a value. This will be evaluated when the related object is deleted.
    reviewer, _ = Reviewer.objects.get_or_create(name="Automated Fallback System")
    return reviewer.id

class AnalyticsTracker(models.Model):
    tracker_code = models.CharField(max_length=50)

    def __str__(self):
        return self.tracker_code

class Type(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    # SET_DEFAULT: When the referenced Theme is deleted, set theme to the default value. Requires a default to be set.
    theme = models.ForeignKey(Theme, on_delete=models.SET_DEFAULT, default=get_default_theme, null=True)
    # SET(): When the referenced Reviewer is deleted, set reviewer to the result of get_fallback_reviewer.
    reviewer = models.ForeignKey(Reviewer, on_delete=models.SET(get_fallback_reviewer), null=True, blank=True)
    # DO_NOTHING: Take no action. Warning: this can cause an IntegrityError if the database enforces referential integrity!
    tracker = models.ForeignKey(AnalyticsTracker, on_delete=models.DO_NOTHING, null=True, blank=True)
    # PROTECT: Prevent deletion of the referenced Type if it is still assigned to any Post. Raises ProtectedError.
    post_type = models.ForeignKey(Type, on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
