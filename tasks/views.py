from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import CATEGORY_COLORS, Category, Task, TasksPreference


@staff_member_required
def index(request):
    order = (F('due_at').asc(nulls_last=True), '-created_at')
    open_tasks = Task.objects.filter(completed=False).prefetch_related('categories').order_by(*order)
    completed_tasks = Task.objects.filter(completed=True).prefetch_related('categories').order_by(*order)
    return render(request, 'tasks/index.html', {
        'open_tasks': open_tasks,
        'completed_tasks': completed_tasks,
        'priority_choices': Task.Priority.choices,
        'categories': Category.objects.all(),
    })


@staff_member_required
def preferences(request):
    settings, _ = TasksPreference.objects.get_or_create(pk=1)
    return render(request, 'tasks/preferences.html', {
        'categories': Category.objects.all(),
        'category_colors': CATEGORY_COLORS,
        'preferences': settings,
        'reminder_choices': TasksPreference.ReminderLeadTime.choices,
    })


@staff_member_required
@require_POST
def create(request):
    title = request.POST.get('title', '').strip()
    if not title or len(title) > 240:
        return JsonResponse({'error': 'Enter a task title (up to 240 characters).'}, status=400)
    task = Task.objects.create(title=title)
    return JsonResponse({
        'id': task.pk,
        'title': task.title,
        'update_url': reverse('tasks:update', args=[task.pk]),
        'priority': task.priority,
        'reminder_enabled': task.reminder_enabled,
        'due_at': '',
        'categories': [],
    })


@staff_member_required
@require_POST
def update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    field = request.POST.get('field')
    value = request.POST.get('value', '')

    if field == 'title':
        value = value.strip()
        if not value or len(value) > 240:
            return JsonResponse({'error': 'A title is required (up to 240 characters).'}, status=400)
        task.title = value
    elif field == 'categories':
        try:
            category_ids = [int(category_id) for category_id in request.POST.getlist('value[]')]
        except ValueError:
            return JsonResponse({'error': 'Choose valid categories.'}, status=400)
        if Category.objects.filter(pk__in=category_ids).count() != len(set(category_ids)):
            return JsonResponse({'error': 'Choose valid categories.'}, status=400)
        task.categories.set(category_ids)
    elif field == 'priority':
        try:
            priority = int(value)
        except ValueError:
            priority = None
        if priority not in Task.Priority.values:
            return JsonResponse({'error': 'Choose a valid priority.'}, status=400)
        task.priority = priority
    elif field == 'due_at':
        try:
            task.due_at = forms.DateTimeField(
                required=False,
                input_formats=['%Y-%m-%dT%H:%M'],
            ).clean(value)
        except forms.ValidationError:
            return JsonResponse({'error': 'Enter a valid due date and time.'}, status=400)
        task.reminder_sent = False
    elif field == 'reminder_enabled':
        if value not in ('true', 'false'):
            return JsonResponse({'error': 'Choose a valid reminder state.'}, status=400)
        task.reminder_enabled = value == 'true'
        task.reminder_sent = False
    elif field == 'completed':
        if value not in ('true', 'false'):
            return JsonResponse({'error': 'Choose a valid completion state.'}, status=400)
        task.completed = value == 'true'
    else:
        return JsonResponse({'error': 'That field cannot be updated.'}, status=400)

    task.save()
    return JsonResponse({'ok': True, 'completed': task.completed})


@staff_member_required
@require_POST
def update_preferences(request):
    value = request.POST.get('default_reminder_minutes', '')
    valid_values = [str(choice) for choice, _ in TasksPreference.ReminderLeadTime.choices]
    if value not in valid_values:
        return JsonResponse({'error': 'Choose a valid default reminder lead time.'}, status=400)
    settings, _ = TasksPreference.objects.get_or_create(pk=1)
    settings.default_reminder_minutes = int(value)
    settings.save(update_fields=['default_reminder_minutes'])
    return JsonResponse({'ok': True})


@staff_member_required
@require_POST
def create_category(request):
    name = request.POST.get('name', '').strip()
    if not name or len(name) > 80:
        return JsonResponse({'error': 'Enter a category name (up to 80 characters).'}, status=400)
    if Category.objects.filter(name__iexact=name).exists():
        return JsonResponse({'error': 'That category already exists.'}, status=400)
    category = Category.objects.create(name=name)
    return JsonResponse({
        'id': category.pk,
        'name': category.name,
        'color': category.color,
        'update_url': reverse('tasks:update-category', args=[category.pk]),
        'delete_url': reverse('tasks:delete-category', args=[category.pk]),
    })


@staff_member_required
@require_POST
def update_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    fields_to_update = []

    if 'name' in request.POST:
        name = request.POST.get('name', '').strip()
        if not name or len(name) > 80:
            return JsonResponse({'error': 'Enter a category name (up to 80 characters).'}, status=400)
        if Category.objects.filter(name__iexact=name).exclude(pk=category.pk).exists():
            return JsonResponse({'error': 'That category already exists.'}, status=400)
        category.name = name
        fields_to_update.append('name')

    if 'color' in request.POST:
        color = request.POST['color']
        if color not in dict(CATEGORY_COLORS):
            return JsonResponse({'error': 'Choose a color from the palette.'}, status=400)
        category.color = color
        fields_to_update.append('color')

    if not fields_to_update:
        return JsonResponse({'error': 'Choose a category name or color to update.'}, status=400)

    category.save(update_fields=fields_to_update)
    return JsonResponse({'ok': True, 'name': category.name, 'color': category.color})


@staff_member_required
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    category.delete()
    return JsonResponse({'ok': True})