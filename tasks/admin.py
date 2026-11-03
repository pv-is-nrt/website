from django.contrib import admin

from .models import Category, Task, TasksPreference


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'priority', 'due_at', 'reminder_enabled', 'completed', 'completed_at', 'cancelled_at', 'archived_at', 'updated_at')
    list_filter = ('completed', 'cancelled_at', 'archived_at', 'priority', 'categories', 'parent')
    search_fields = ('title', 'notes', 'categories__name')
    filter_horizontal = ('categories',)


@admin.register(TasksPreference)
class TasksPreferenceAdmin(admin.ModelAdmin):
    list_display = ('default_reminder_minutes',)