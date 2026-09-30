from django.contrib import admin

from .models import Category, Task, TasksPreference


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'due_at', 'reminder_enabled', 'completed', 'updated_at')
    list_filter = ('completed', 'priority', 'categories')
    search_fields = ('title', 'categories__name')
    filter_horizontal = ('categories',)


@admin.register(TasksPreference)
class TasksPreferenceAdmin(admin.ModelAdmin):
    list_display = ('default_reminder_minutes',)