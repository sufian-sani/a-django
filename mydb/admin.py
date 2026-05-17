from django.contrib import admin
from .models.blog import Author, Category, Post, Theme, Reviewer, AnalyticsTracker, Type

# Register your models here.


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')
    search_fields = ('name', 'email')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Reviewer)
class ReviewerAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(AnalyticsTracker)
class AnalyticsTrackerAdmin(admin.ModelAdmin):
    list_display = ('tracker_code',)

@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'theme', 'reviewer', 'tracker', 'post_type', 'created_at', 'updated_at')
    list_filter = ('category', 'theme', 'reviewer', 'tracker', 'post_type', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'author__name')
    ordering = ('-created_at',)
