import calendar
import random
import re
from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Count, DurationField, ExpressionWrapper, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import CATEGORY_PALETTE, PRIORITY_ICON_PALETTE, Category, Task, TasksPreference, TasksTheme
from .theme_palette import DEFAULT_THEME_SEED, build_theme_palette


def _theme_owner_id(request):
    return str(getattr(request.user, 'pk', ''))


def _user_themes(request):
    return TasksTheme.objects.filter(owner_id=_theme_owner_id(request))


def _active_theme(request):
    themes = _user_themes(request)
    active_theme = themes.filter(is_active=True).first()
    if active_theme:
        return active_theme
    theme_id = getattr(request, 'session', {}).get('tasks_active_theme')
    active_theme = themes.filter(pk=theme_id).first() if theme_id else None
    if active_theme:
        themes.update(is_active=False)
        active_theme.is_active = True
        active_theme.save(update_fields=['is_active'])
    return active_theme


def _theme_seed(active_theme):
    return active_theme.seed_color if active_theme else DEFAULT_THEME_SEED


def archive_expired_completed_tasks(preferences, now=None):
    now = now or timezone.now()
    value = preferences.auto_archive_after
    amount, unit = int(value[:-1]), value[-1]
    if unit == 'w':
        cutoff = now - timedelta(weeks=amount)
    else:
        months = amount * (12 if unit == 'y' else 1)
        month_index = now.month - 1 - months
        year = now.year + month_index // 12
        month = month_index % 12 + 1
        day = min(now.day, calendar.monthrange(year, month)[1])
        cutoff = now.replace(year=year, month=month, day=day)
    Task.objects.filter(
        parent__isnull=True,
        completed=True,
        cancelled_at__isnull=True,
        archived_at__isnull=True,
        completed_at__lte=cutoff,
    ).update(archived_at=now)


@staff_member_required
def index(request):
    preferences, _ = TasksPreference.objects.get_or_create(pk=1)
    active_theme = _active_theme(request)
    theme_seed = _theme_seed(active_theme)
    archive_expired_completed_tasks(preferences)
    view_name = request.GET.get('view', preferences.default_view)
    if view_name not in ('open', 'today', 'upcoming', 'completed', 'cancelled', 'archived'):
        view_name = 'open'
    if view_name == 'cancelled' and not preferences.show_cancelled_tab:
        view_name = 'open'
    if view_name == 'archived' and not preferences.show_archived_tab:
        view_name = 'open'
    today = timezone.localdate()
    date_range_choices = (
        ('all', 'Any time'),
        ('today', 'Today'),
        ('this_week', 'This week'),
        ('this_month', 'This month'),
        ('this_year', 'This year'),
        ('last_30_days', 'Last 30 days'),
        ('last_90_days', 'Last 90 days'),
        ('custom', 'Custom'),
    )
    sort_defaults = {
        'open': ('created_at', 'desc'),
        'today': ('due_at', 'asc'),
        'upcoming': ('due_at', 'asc'),
        'completed': ('completed_at', 'desc'),
        'cancelled': ('cancelled_at', 'desc'),
        'archived': ('archived_at', 'desc'),
    }
    open_sort_choices = (
        ('due_at', 'Due date'),
        ('created_at', 'Created date'),
        ('priority', 'Priority'),
        ('duration_open', 'Duration open'),
    )
    sort_choices_by_view = {
        'open': open_sort_choices,
        'today': open_sort_choices,
        'upcoming': open_sort_choices,
        'completed': (
            ('completed_at', 'Completed on'),
            ('due_at', 'Due date'),
            ('created_at', 'Created date'),
            ('priority', 'Priority'),
            ('time_taken', 'Time taken'),
        ),
        'cancelled': (
            ('cancelled_at', 'Cancelled on'),
            ('created_at', 'Created date'),
            ('priority', 'Priority'),
        ),
        'archived': (
            ('archived_at', 'Archived on'),
            ('created_at', 'Created date'),
            ('priority', 'Priority'),
        ),
    }
    sort_choices = sort_choices_by_view[view_name]
    default_sort_by, default_sort_direction = sort_defaults[view_name]
    valid_sort_by = {value for value, _ in sort_choices}
    requested_sort_by = request.GET.get('sort_by', '').strip()
    sort_by = requested_sort_by if requested_sort_by in valid_sort_by else default_sort_by
    sort_direction_choices = (('asc', 'Ascending'), ('desc', 'Descending'))
    sort_direction = request.GET.get('sort_direction', default_sort_direction).strip()
    if sort_direction not in {value for value, _ in sort_direction_choices}:
        sort_direction = default_sort_direction
    sort_active = sort_by != default_sort_by or sort_direction != default_sort_direction
    date_range = request.GET.get('date_range', '').strip()
    valid_date_ranges = {value for value, _ in date_range_choices}
    if not date_range:
        date_range = 'custom' if request.GET.get('created_after') or request.GET.get('created_before') else 'all'
    if date_range not in valid_date_ranges:
        date_range = 'all'

    def parse_date_filter(name):
        raw_value = request.GET.get(name, '').strip()
        if not raw_value:
            return '', None
        try:
            return raw_value, forms.DateField().clean(raw_value)
        except forms.ValidationError:
            return '', None

    created_after = ''
    created_before = ''
    created_after_date = None
    created_before_date = None
    if date_range == 'custom':
        created_after, created_after_date = parse_date_filter('created_after')
        created_before, created_before_date = parse_date_filter('created_before')
    elif date_range != 'all':
        if date_range == 'today':
            created_after_date = today
        elif date_range == 'this_week':
            created_after_date = today - timedelta(days=today.weekday())
        elif date_range == 'this_month':
            created_after_date = today.replace(day=1)
        elif date_range == 'this_year':
            created_after_date = today.replace(month=1, day=1)
        elif date_range == 'last_30_days':
            created_after_date = today - timedelta(days=29)
        elif date_range == 'last_90_days':
            created_after_date = today - timedelta(days=89)
        created_after = created_after_date.isoformat()
    all_category_ids = list(Category.objects.values_list('pk', flat=True))
    requested_categories = request.GET.getlist('category')
    category_ids = []
    for raw_category_id in requested_categories:
        try:
            category_id = int(raw_category_id)
        except ValueError:
            continue
        if category_id not in category_ids and Category.objects.filter(pk=category_id).exists():
            category_ids.append(category_id)
    tag_filter_active = (
        request.GET.get('tag_filter') == '1'
        and set(category_ids) != set(all_category_ids)
    )
    if not tag_filter_active:
        category_ids = all_category_ids
    selected_categories = [str(category_id) for category_id in category_ids]

    def tasks_for_state(state):
        tasks = Task.objects.filter(parent__isnull=True)
        if state in ('open', 'today', 'upcoming'):
            tasks = tasks.filter(completed=False, cancelled_at__isnull=True, archived_at__isnull=True)
            if state == 'today':
                tasks = tasks.filter(due_at__date__lte=today, due_at__isnull=False)
            elif state == 'upcoming':
                tasks = tasks.filter(due_at__date__gt=today)
        elif state == 'completed':
            tasks = tasks.filter(completed=True, archived_at__isnull=True)
        elif state == 'cancelled':
            tasks = tasks.filter(cancelled_at__isnull=False, archived_at__isnull=True)
        else:
            tasks = tasks.filter(archived_at__isnull=False)
        if created_after_date:
            tasks = tasks.filter(created_at__date__gte=created_after_date)
        if created_before_date:
            tasks = tasks.filter(created_at__date__lte=created_before_date)
        if tag_filter_active:
            if category_ids:
                tasks = tasks.filter(categories__pk__in=category_ids).distinct()
            else:
                tasks = tasks.none()
        sort_expressions = {
            'created_at': F('created_at'),
            'due_at': F('due_at'),
            'priority': F('priority'),
            'completed_at': F('completed_at'),
            'cancelled_at': F('cancelled_at'),
            'archived_at': F('archived_at'),
            'duration_open': F('created_at'),
            'time_taken': ExpressionWrapper(
                F('completed_at') - F('created_at'),
                output_field=DurationField(),
            ),
        }
        expression = sort_expressions[sort_by]
        descending = sort_direction == 'desc'
        if sort_by == 'priority':
            descending = not descending
        if sort_by == 'duration_open':
            primary_order = expression.asc() if descending else expression.desc()
        elif sort_by in {'due_at', 'completed_at', 'cancelled_at', 'archived_at', 'time_taken'}:
            primary_order = expression.desc(nulls_last=True) if descending else expression.asc(nulls_last=True)
        else:
            primary_order = expression.desc() if descending else expression.asc()
        order = (primary_order, '-created_at')
        return tasks.annotate(
            open_subtask_count=Count(
                'subtasks',
                filter=Q(subtasks__completed=False),
                distinct=True,
            ),
        ).prefetch_related('categories', 'subtasks__categories').order_by(*order)

    tasks = tasks_for_state(view_name)
    filter_params = {}
    if created_after:
        filter_params['created_after'] = created_after
    if created_before:
        filter_params['created_before'] = created_before
    if date_range != 'all':
        filter_params['date_range'] = date_range
    if sort_active:
        filter_params['sort_by'] = sort_by
        filter_params['sort_direction'] = sort_direction
    if tag_filter_active:
        filter_params['tag_filter'] = '1'
        filter_params['category'] = selected_categories

    def tab_url(tab):
        return '{}?{}'.format(
            reverse('tasks:index'),
            urlencode({**filter_params, 'view': tab}, doseq=True),
        )

    clear_url = '{}?{}'.format(reverse('tasks:index'), urlencode({'view': view_name}))
    # Each entry is a fully-written static example shown verbatim. Just add,
    # edit, or remove lines here; one is picked at random on each page load.
    capture_examples = (
        'Call dentist /Dec-15 p2 @health',
        'Water plants /Sat weekly @home p3',
        'Pay rent /11-01 p1 monthly @personal',
        'Buy coffee /today p4 @work',
        'Send invoice /tomorrow p3 @work',
        'Renew passport /Apr-30 @personal p1',
        'Grocery run /Fri @shopping p2',
        'Book flights /next-Fri p2 @personal',
        'Update portfolio p5 @work',
        'Take out trash /Mon weekly @home',
    )
    capture_example = random.choice(capture_examples)
    return render(request, 'tasks/index.html', {
        'tasks': tasks,
        'view_name': view_name,
        'open_url': tab_url('open'),
        'today_url': tab_url('today'),
        'upcoming_url': tab_url('upcoming'),
        'completed_url': tab_url('completed'),
        'cancelled_url': tab_url('cancelled'),
        'archived_url': tab_url('archived'),
        'clear_url': clear_url,
        'created_after': created_after,
        'created_before': created_before,
        'date_range': date_range,
        'date_range_choices': date_range_choices,
        'sort_by': sort_by,
        'sort_direction': sort_direction,
        'sort_choices': sort_choices,
        'sort_direction_choices': sort_direction_choices,
        'selected_categories': selected_categories,
        'tag_filter_active': tag_filter_active,
        'filters_open': preferences.filters_expanded_by_default or bool(
            created_after or created_before or tag_filter_active or date_range == 'custom'
            or sort_active
        ),
        'sort_active': sort_active,
        'show_quick_capture_hint': preferences.show_quick_capture_hint,
        'show_priority_numbers': preferences.show_priority_numbers,
        'priority_icon_style': preferences.priority_icon_style,
        'show_task_age': preferences.show_task_age,
        'show_archived_tab': preferences.show_archived_tab,
        'show_cancelled_tab': preferences.show_cancelled_tab,
        'quick_capture_example': capture_example,
        'theme': preferences.theme,
        'selected_theme': active_theme,
        'theme_seed_color': theme_seed,
        'theme_palette': build_theme_palette(theme_seed),
        'background_pattern': preferences.background_pattern,
        'local_today': today.isoformat(),
        'open_count': tasks_for_state('open').count(),
        'today_count': tasks_for_state('today').count(),
        'upcoming_count': tasks_for_state('upcoming').count(),
        'completed_count': tasks_for_state('completed').count(),
        'cancelled_count': tasks_for_state('cancelled').count(),
        'archived_count': tasks_for_state('archived').count(),
        'priority_choices': [
            (value, 'P{}'.format(6 - value))
            for value, _ in reversed(Task.Priority.choices)
        ],
        'priority_icon_palette': PRIORITY_ICON_PALETTE,
        'recurrence_choices': Task.Recurrence.choices,
        'categories': Category.objects.all(),
    })


@staff_member_required
def preferences(request):
    settings, _ = TasksPreference.objects.get_or_create(pk=1)
    active_theme = _active_theme(request)
    theme_seed = _theme_seed(active_theme)
    category_default_color = Category._meta.get_field('color').default
    category_default_dark_color = next(
        (dark for light, dark, _ in CATEGORY_PALETTE if light == category_default_color),
        category_default_color,
    )
    return render(request, 'tasks/preferences.html', {
        'categories': Category.objects.all(),
        'category_palette': CATEGORY_PALETTE,
        'category_default_color': category_default_color,
        'category_default_dark_color': category_default_dark_color,
        'preferences': settings,
        'reminder_choices': TasksPreference.ReminderLeadTime.choices,
        'recurrence_reminder_preferences': (
            ('Daily', 'daily_reminder_minutes', settings.daily_reminder_minutes),
            ('Weekly', 'weekly_reminder_minutes', settings.weekly_reminder_minutes),
            ('Monthly', 'monthly_reminder_minutes', settings.monthly_reminder_minutes),
            ('Yearly', 'yearly_reminder_minutes', settings.yearly_reminder_minutes),
        ),
        'priority_choices': [
            (value, 'P{}'.format(6 - value))
            for value, _ in reversed(Task.Priority.choices)
        ],
        'priority_icon_style_choices': TasksPreference.PriorityIconStyle.choices,
        'recurrence_choices': Task.Recurrence.choices,
        'default_view_choices': TasksPreference.DefaultView.choices,
        'show_quick_capture_hint': settings.show_quick_capture_hint,
        'show_task_age': settings.show_task_age,
        'filters_expanded_by_default': settings.filters_expanded_by_default,
        'auto_archive_choices': TasksPreference.AutoArchiveAfter.choices,
        'show_archived_tab': settings.show_archived_tab,
        'show_cancelled_tab': settings.show_cancelled_tab,
        'theme_choices': TasksPreference.Theme.choices,
        'custom_themes': _user_themes(request),
        'selected_theme': active_theme,
        'default_theme_seed': DEFAULT_THEME_SEED,
        'theme_seed_color': theme_seed,
        'theme_palette': build_theme_palette(theme_seed),
        'background_pattern_choices': TasksPreference.BackgroundPattern.choices,
    })


@staff_member_required
@require_POST
def create(request):
    title = request.POST.get('title', '').strip()
    if not title or len(title) > 240:
        return JsonResponse({'error': 'Enter a task title (up to 240 characters).'}, status=400)
    parent = None
    parent_id = request.POST.get('parent_id', '').strip()
    if parent_id:
        try:
            parent_id = int(parent_id)
        except ValueError:
            return JsonResponse({'error': 'Choose a valid parent task.'}, status=400)
        parent = Task.objects.filter(pk=parent_id, parent__isnull=True).first()
        if parent is None:
            return JsonResponse({'error': 'Choose a valid top-level task.'}, status=400)

    preferences, _ = TasksPreference.objects.get_or_create(pk=1)
    try:
        priority = int(request.POST.get('priority') or preferences.default_priority)
    except (TypeError, ValueError):
        priority = None
    if priority not in Task.Priority.values:
        return JsonResponse({'error': 'Choose a valid priority.'}, status=400)

    recurrence_default = Task.Recurrence.NONE if parent else preferences.default_recurrence
    recurrence = request.POST.get('recurrence', '').strip() or recurrence_default
    if recurrence not in Task.Recurrence.values:
        return JsonResponse({'error': 'Choose a valid recurrence.'}, status=400)

    try:
        due_at = forms.DateTimeField(
            required=False,
            input_formats=['%Y-%m-%dT%H:%M'],
        ).clean(request.POST.get('due_at', '').strip())
    except forms.ValidationError:
        return JsonResponse({'error': 'Enter a valid due date and time.'}, status=400)

    try:
        category_ids = [int(category_id) for category_id in request.POST.getlist('categories[]')]
    except ValueError:
        return JsonResponse({'error': 'Choose valid tags.'}, status=400)
    if Category.objects.filter(pk__in=category_ids).count() != len(set(category_ids)):
        return JsonResponse({'error': 'Choose valid tags.'}, status=400)

    with transaction.atomic():
        task = Task.objects.create(
            title=title,
            parent=parent,
            priority=priority,
            recurrence=recurrence,
            due_at=due_at,
        )
        task.categories.set(category_ids)
    return JsonResponse({
        'id': task.pk,
        'title': task.title,
        'update_url': reverse('tasks:update', args=[task.pk]),
        'priority': task.priority,
        'recurrence': task.recurrence,
        'reminder_enabled': task.reminder_enabled,
        'due_at': task.due_at.isoformat() if task.due_at else '',
        'categories': category_ids,
        'parent_id': parent.pk if parent else None,
    })


def create_recurrence_successor(task):
    due_at = task.next_occurrence_due_at(task.completed_at)
    if due_at is None:
        return None

    with transaction.atomic():
        successor, created = Task.objects.get_or_create(
            recurrence_source=task,
            defaults={
                'title': task.title,
                'notes': task.notes,
                'priority': task.priority,
                'recurrence': task.recurrence,
                'recurrence_anchor_day': task.recurrence_anchor_day or due_at.day,
                'due_at': due_at,
                'reminder_enabled': task.reminder_enabled,
                'reminder_recipient_email': task.reminder_recipient_email,
            },
        )
        if created:
            successor.categories.set(task.categories.all())
            for subtask in task.subtasks.all():
                next_subtask = Task.objects.create(
                    title=subtask.title,
                    notes=subtask.notes,
                    parent=successor,
                )
                next_subtask.categories.set(subtask.categories.all())
    return successor


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
    elif field == 'notes':
        if len(value) > 20000:
            return JsonResponse({'error': 'Notes must be 20,000 characters or fewer.'}, status=400)
        task.notes = value
    elif field == 'categories':
        try:
            category_ids = [int(category_id) for category_id in request.POST.getlist('value[]')]
        except ValueError:
            return JsonResponse({'error': 'Choose valid tags.'}, status=400)
        if Category.objects.filter(pk__in=category_ids).count() != len(set(category_ids)):
            return JsonResponse({'error': 'Choose valid tags.'}, status=400)
        task.categories.set(category_ids)
    elif field == 'priority':
        try:
            priority = int(value)
        except ValueError:
            priority = None
        if priority not in Task.Priority.values:
            return JsonResponse({'error': 'Choose a valid priority.'}, status=400)
        task.priority = priority
    elif field == 'recurrence':
        if value not in Task.Recurrence.values:
            return JsonResponse({'error': 'Choose a valid recurrence.'}, status=400)
        task.recurrence = value
        successor = Task.objects.filter(recurrence_source=task, completed=False).first()
        if successor:
            successor.recurrence = value
            fields_to_update = ['recurrence', 'updated_at']
            if value != Task.Recurrence.NONE:
                successor.due_at = task.next_occurrence_due_at(task.completed_at)
                fields_to_update.append('due_at')
            successor.save(update_fields=fields_to_update)
    elif field == 'due_at':
        try:
            task.due_at = forms.DateTimeField(
                required=False,
                input_formats=['%Y-%m-%dT%H:%M'],
            ).clean(value)
        except forms.ValidationError:
            return JsonResponse({'error': 'Enter a valid due date and time.'}, status=400)
        task.reminder_sent = False
        if task.due_at is None:
            task.reminder_enabled = False
        if task.recurrence != Task.Recurrence.NONE and task.due_at:
            task.recurrence_anchor_day = task.due_at.day
    elif field == 'completed_at':
        if not task.completed:
            return JsonResponse({'error': 'Only completed tasks have a completion date.'}, status=400)
        try:
            task.completed_at = forms.DateTimeField(
                input_formats=['%Y-%m-%dT%H:%M'],
            ).clean(value)
        except forms.ValidationError:
            return JsonResponse({'error': 'Enter a valid completion date and time.'}, status=400)
    elif field == 'created_at':
        try:
            task.created_at = forms.DateTimeField(
                input_formats=['%Y-%m-%dT%H:%M'],
            ).clean(value)
        except forms.ValidationError:
            return JsonResponse({'error': 'Enter a valid creation date and time.'}, status=400)
    elif field == 'reminder_enabled':
        if value not in ('true', 'false'):
            return JsonResponse({'error': 'Choose a valid reminder state.'}, status=400)
        if value == 'true' and task.due_at is None:
            return JsonResponse({'error': 'Set a due date before enabling a reminder.'}, status=400)
        task.reminder_enabled = value == 'true'
        if task.reminder_enabled:
            user = getattr(request, 'user', None)
            task.reminder_recipient_email = (getattr(user, 'email', '') or '').strip()
        task.reminder_sent = False
    elif field in ('completed', 'undo_completion'):
        if value not in ('true', 'false'):
            return JsonResponse({'error': 'Choose a valid completion state.'}, status=400)
        if field == 'undo_completion' and (value != 'false' or not task.completed):
            return JsonResponse({'error': 'Only a completed task can be undone.'}, status=400)
        if value == 'true':
            if not task.completed:
                task.completed_at = timezone.now()
            task.completed = True
            task.cancelled_at = None
            task.archived_at = None
        else:
            task.completed = False
            task.completed_at = None
            task.archived_at = None
    elif field == 'cancelled':
        if value not in ('true', 'false'):
            return JsonResponse({'error': 'Choose a valid cancellation state.'}, status=400)
        if value == 'true':
            if task.completed or task.archived_at:
                return JsonResponse({'error': 'Only open tasks can be cancelled.'}, status=400)
            task.cancelled_at = timezone.now()
        else:
            task.cancelled_at = None
    elif field == 'archived':
        if value not in ('true', 'false'):
            return JsonResponse({'error': 'Choose a valid archive state.'}, status=400)
        if value == 'true':
            if not task.completed:
                return JsonResponse({'error': 'Only completed tasks can be archived.'}, status=400)
            task.archived_at = timezone.now()
        else:
            task.archived_at = None
    elif field == 'delete':
        if value != 'true' or (
            task.parent_id is None and not task.cancelled_at and not task.archived_at
        ):
            return JsonResponse({'error': 'Only cancelled or archived tasks can be permanently deleted.'}, status=400)
        task.delete()
        return JsonResponse({'ok': True, 'deleted': True})
    else:
        return JsonResponse({'error': 'That field cannot be updated.'}, status=400)

    task.save()
    if field == 'undo_completion':
        try:
            successor_id = int(request.POST.get('successor_id', ''))
        except ValueError:
            successor_id = None
        if successor_id:
            Task.objects.filter(
                pk=successor_id,
                recurrence_source=task,
                completed=False,
                cancelled_at__isnull=True,
                archived_at__isnull=True,
            ).delete()
    successor = None
    if field in ('completed', 'recurrence') and task.completed and task.recurrence != Task.Recurrence.NONE:
        successor = create_recurrence_successor(task)
    return JsonResponse({
        'ok': True,
        'completed': task.completed,
        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
        'cancelled_at': task.cancelled_at.isoformat() if task.cancelled_at else None,
        'archived_at': task.archived_at.isoformat() if task.archived_at else None,
        'days_open': task.days_open,
        'days_to_complete': task.days_to_complete,
        'next_task_id': successor.pk if successor else None,
    })


@staff_member_required
@require_POST
def update_preferences(request):
    settings, _ = TasksPreference.objects.get_or_create(pk=1)
    fields_to_update = []

    if 'active_theme' in request.POST:
        value = request.POST.get('active_theme', '').strip()
        active_theme = None
        if value:
            active_theme = _user_themes(request).filter(pk=value).first()
            if active_theme is None:
                return JsonResponse({'error': 'Choose one of your saved themes.'}, status=400)
        _user_themes(request).update(is_active=False)
        if active_theme:
            active_theme.is_active = True
            active_theme.save(update_fields=['is_active'])
        request.session.pop('tasks_active_theme', None)
        seed = _theme_seed(active_theme)
        return JsonResponse({
            'ok': True,
            'active_theme': active_theme.pk if active_theme else '',
            'seed_color': seed,
            'palette': build_theme_palette(seed),
        })

    reminder_fields = (
        'default_reminder_minutes',
        'daily_reminder_minutes',
        'weekly_reminder_minutes',
        'monthly_reminder_minutes',
        'yearly_reminder_minutes',
    )
    valid_values = [str(choice) for choice, _ in TasksPreference.ReminderLeadTime.choices]
    for field in reminder_fields:
        if field in request.POST:
            value = request.POST.get(field, '')
            if value not in valid_values:
                return JsonResponse({'error': 'Choose a valid reminder lead time.'}, status=400)
            setattr(settings, field, int(value))
            fields_to_update.append(field)

    if 'default_priority' in request.POST:
        value = request.POST.get('default_priority', '')
        if value not in [str(choice) for choice in Task.Priority.values]:
            return JsonResponse({'error': 'Choose a valid default priority.'}, status=400)
        settings.default_priority = int(value)
        fields_to_update.append('default_priority')

    if 'priority_icon_style' in request.POST:
        value = request.POST.get('priority_icon_style', '')
        if value not in TasksPreference.PriorityIconStyle.values:
            return JsonResponse({'error': 'Choose a valid priority icon style.'}, status=400)
        settings.priority_icon_style = value
        fields_to_update.append('priority_icon_style')

    if 'default_recurrence' in request.POST:
        value = request.POST.get('default_recurrence', '')
        if value not in Task.Recurrence.values:
            return JsonResponse({'error': 'Choose a valid default recurrence.'}, status=400)
        settings.default_recurrence = value
        fields_to_update.append('default_recurrence')

    if 'default_view' in request.POST:
        value = request.POST.get('default_view', '')
        if value not in TasksPreference.DefaultView.values:
            return JsonResponse({'error': 'Choose a valid default task view.'}, status=400)
        settings.default_view = value
        fields_to_update.append('default_view')

    if 'auto_archive_after' in request.POST:
        value = request.POST.get('auto_archive_after', '')
        if value not in TasksPreference.AutoArchiveAfter.values:
            return JsonResponse({'error': 'Choose a valid archive delay.'}, status=400)
        settings.auto_archive_after = value
        fields_to_update.append('auto_archive_after')

    if 'theme' in request.POST:
        value = request.POST.get('theme', '')
        if value not in TasksPreference.Theme.values:
            return JsonResponse({'error': 'Choose a valid theme.'}, status=400)
        settings.theme = value
        fields_to_update.append('theme')

    if 'background_pattern' in request.POST:
        value = request.POST.get('background_pattern', '')
        if value not in TasksPreference.BackgroundPattern.values:
            return JsonResponse({'error': 'Choose a valid background pattern.'}, status=400)
        settings.background_pattern = value
        fields_to_update.append('background_pattern')

    for field in (
        'show_quick_capture_hint',
        'show_priority_numbers',
        'show_task_age',
        'filters_expanded_by_default',
        'show_archived_tab',
        'show_cancelled_tab',
    ):
        if field in request.POST:
            value = request.POST.get(field, '')
            if value not in ('true', 'false'):
                return JsonResponse({'error': 'Choose a valid display preference.'}, status=400)
            setattr(settings, field, value == 'true')
            fields_to_update.append(field)

    if not fields_to_update:
        return JsonResponse({'error': 'Choose a preference to update.'}, status=400)
    settings.save(update_fields=fields_to_update)
    return JsonResponse({'ok': True})


@staff_member_required
@require_POST
def create_theme(request):
    name = request.POST.get('name', '').strip()
    color = request.POST.get('color', '').strip()
    if not name or len(name) > 40:
        return JsonResponse({'error': 'Enter a theme name up to 40 characters.'}, status=400)
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        return JsonResponse({'error': 'Enter a six-digit hex color.'}, status=400)
    if _user_themes(request).filter(name__iexact=name).exists():
        return JsonResponse({'error': 'You already have a theme with that name.'}, status=400)

    _user_themes(request).update(is_active=False)
    theme = TasksTheme.objects.create(
        owner_id=_theme_owner_id(request),
        name=name,
        seed_color=color.lower(),
        is_active=True,
    )
    request.session.pop('tasks_active_theme', None)
    palette = build_theme_palette(theme.seed_color)
    return JsonResponse({
        'ok': True,
        'theme': {
            'id': theme.pk,
            'name': theme.name,
            'seed_color': theme.seed_color,
            'delete_url': reverse('tasks:delete-theme', args=[theme.pk]),
        },
        'seed_color': theme.seed_color,
        'palette': palette,
    }, status=201)


@staff_member_required
@require_POST
def delete_theme(request, theme_id):
    theme = _user_themes(request).filter(pk=theme_id).first()
    if theme is None:
        return JsonResponse({'error': 'That saved theme was not found.'}, status=404)
    was_active = theme.is_active or str(getattr(request, 'session', {}).get('tasks_active_theme', '')) == str(theme.pk)
    theme.delete()
    if was_active:
        request.session.pop('tasks_active_theme', None)
    seed = DEFAULT_THEME_SEED if was_active else _theme_seed(_active_theme(request))
    return JsonResponse({
        'ok': True,
        'was_active': was_active,
        'seed_color': seed,
        'palette': build_theme_palette(seed),
    })


@staff_member_required
@require_POST
def create_category(request):
    name = request.POST.get('name', '').strip()
    if not name or len(name) > 80:
        return JsonResponse({'error': 'Enter a tag name (up to 80 characters).'}, status=400)
    if Category.objects.filter(name__iexact=name).exists():
        return JsonResponse({'error': 'That tag already exists.'}, status=400)
    category = Category.objects.create(name=name)
    return JsonResponse({
        'id': category.pk,
        'name': category.name,
        'color': category.color,
        'dark_color': category.dark_color,
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
            return JsonResponse({'error': 'Enter a tag name (up to 80 characters).'}, status=400)
        if Category.objects.filter(name__iexact=name).exclude(pk=category.pk).exists():
            return JsonResponse({'error': 'That tag already exists.'}, status=400)
        category.name = name
        fields_to_update.append('name')

    if 'color' in request.POST:
        color = request.POST['color']
        if color not in {light for light, dark, label in CATEGORY_PALETTE}:
            return JsonResponse({'error': 'Choose a color from the palette.'}, status=400)
        category.color = color
        fields_to_update.append('color')

    if not fields_to_update:
        return JsonResponse({'error': 'Choose a tag name or color to update.'}, status=400)

    category.save(update_fields=fields_to_update)
    return JsonResponse({
        'ok': True,
        'name': category.name,
        'color': category.color,
        'dark_color': category.dark_color,
    })


@staff_member_required
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    category.delete()
    return JsonResponse({'ok': True})