import json
from datetime import datetime, time, timedelta
from unittest.mock import patch
from types import SimpleNamespace

from django.test import RequestFactory, TestCase
from django.utils import timezone

from .models import CATEGORY_COLORS, CATEGORY_PALETTE, Category, Task, TasksPreference, TasksTheme
from .views import (
    archive_expired_completed_tasks,
    create,
    create_theme,
    delete_theme,
    index,
    update,
    update_preferences,
)
from .theme_palette import DEFAULT_THEME_SEED, _contrast, build_theme_palette


class TaskWorkflowTests(TestCase):
    databases = {'default', 'tasks'}

    def update_task(self, task, field, value):
        request = RequestFactory().post('/tasks/api/', {'field': field, 'value': value})
        return update.__wrapped__.__wrapped__(request, task.pk)

    def update_task_categories(self, task, category_ids):
        request = RequestFactory().post('/tasks/api/', {
            'field': 'categories',
            'value[]': [str(category_id) for category_id in category_ids],
        })
        return update.__wrapped__.__wrapped__(request, task.pk)

    def create_task(self, data):
        request = RequestFactory().post('/tasks/api/create/', data)
        with patch('tasks.views.reverse', return_value='/tasks/api/update/'):
            return create.__wrapped__.__wrapped__(request)

    def tasks_for_view(self, view_name):
        request = RequestFactory().get('/tasks/', {'view': view_name})
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        with patch('tasks.views.reverse', return_value='/tasks/'), patch(
            'tasks.views.render', side_effect=lambda request, template, context: context,
        ):
            context = index.__wrapped__(request)
        return list(context['tasks'])

    def test_duration_uses_local_calendar_days(self):
        today = timezone.localdate()
        created_at = timezone.make_aware(datetime.combine(today - timedelta(days=4), time(12)))
        completed_at = timezone.make_aware(datetime.combine(today - timedelta(days=1), time(12)))
        task = Task.objects.create(
            title='Completed task',
            completed=True,
            completed_at=completed_at,
        )
        Task.objects.filter(pk=task.pk).update(created_at=created_at)
        task.refresh_from_db()

        self.assertEqual(task.days_to_complete, 3)

        open_task = Task.objects.create(title='Open task')
        Task.objects.filter(pk=open_task.pk).update(created_at=created_at)
        open_task.refresh_from_db()
        self.assertEqual(open_task.days_open, 4)

        legacy_task = Task.objects.create(title='Legacy completion', completed=True)
        Task.objects.filter(pk=legacy_task.pk).update(
            created_at=created_at,
            completed_at=None,
        )
        legacy_task.refresh_from_db()
        self.assertEqual(legacy_task.days_to_complete, 4)

    def test_age_progress_transitions_from_green_to_red_by_day_thirty(self):
        task = Task.objects.create(title='Age progress')
        today = timezone.localdate()

        for days, expected_progress in ((0, 0), (15, 50), (30, 100), (45, 100)):
            created_at = timezone.make_aware(datetime.combine(today - timedelta(days=days), time(12)))
            Task.objects.filter(pk=task.pk).update(created_at=created_at)
            task.refresh_from_db()
            self.assertEqual(task.age_progress, expected_progress)

    def test_age_visibility_preference_is_shared_across_task_tabs(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        preferences.show_task_age = False
        preferences.save(update_fields=['show_task_age'])

        for view_name in ('open', 'today', 'upcoming', 'completed', 'cancelled', 'archived'):
            with self.subTest(view=view_name):
                request = RequestFactory().get('/tasks/', {'view': view_name})
                request.user = SimpleNamespace(is_active=True, is_staff=True)
                with patch('tasks.views.reverse', return_value='/tasks/'), patch(
                    'tasks.views.render', side_effect=lambda request, template, context: context,
                ):
                    context = index.__wrapped__(request)
                self.assertFalse(context['show_task_age'])

    def test_category_picker_uses_sixteen_existing_model_colors(self):
        self.assertEqual(len(CATEGORY_PALETTE), 16)
        self.assertTrue(set(dict(CATEGORY_PALETTE)).issubset(dict(CATEGORY_COLORS)))

    def test_archive_preferences_have_requested_defaults(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)

        self.assertEqual(preferences.auto_archive_after, TasksPreference.AutoArchiveAfter.ONE_YEAR)
        self.assertTrue(preferences.show_archived_tab)
        self.assertFalse(preferences.show_cancelled_tab)
        self.assertEqual(preferences.theme, TasksPreference.Theme.AUTO)
        self.assertEqual(preferences.background_pattern, TasksPreference.BackgroundPattern.NONE)

    def test_archive_cutoff_handles_week_and_month_end(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        now = timezone.make_aware(datetime(2026, 3, 31, 12))
        month_boundary = timezone.make_aware(datetime(2026, 2, 28, 12))
        expired = Task.objects.create(title='Month-end completion', completed=True)
        recent = Task.objects.create(title='Recent completion', completed=True)
        Task.objects.filter(pk=expired.pk).update(completed_at=month_boundary)
        Task.objects.filter(pk=recent.pk).update(completed_at=month_boundary + timedelta(minutes=1))
        preferences.auto_archive_after = TasksPreference.AutoArchiveAfter.ONE_MONTH
        archive_expired_completed_tasks(preferences, now)

        expired.refresh_from_db()
        recent.refresh_from_db()
        self.assertEqual(expired.archived_at, now)
        self.assertIsNone(recent.archived_at)

        preferences.auto_archive_after = TasksPreference.AutoArchiveAfter.ONE_WEEK
        weekly_boundary = Task.objects.create(title='Weekly completion', completed=True)
        Task.objects.filter(pk=weekly_boundary.pk).update(completed_at=now - timedelta(days=7))
        archive_expired_completed_tasks(preferences, now)
        weekly_boundary.refresh_from_db()
        self.assertEqual(weekly_boundary.archived_at, now)

    def test_expired_tasks_move_out_of_completed_on_next_tasks_view(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        preferences.auto_archive_after = TasksPreference.AutoArchiveAfter.ONE_MONTH
        preferences.save(update_fields=['auto_archive_after'])
        task = Task.objects.create(title='Automatically archived', completed=True)
        Task.objects.filter(pk=task.pk).update(completed_at=timezone.now() - timedelta(days=32))

        self.assertNotIn(task, self.tasks_for_view('completed'))
        self.assertIn(task, self.tasks_for_view('archived'))

    def test_index_filters_by_created_date_and_category(self):
        today = timezone.localdate()
        category = Category.objects.create(name='Research')
        Category.objects.create(name='Other')
        included = Task.objects.create(title='Included')
        excluded_category = Task.objects.create(title='Other category')
        excluded_date = Task.objects.create(title='Older')
        included.created_at = timezone.make_aware(datetime.combine(today - timedelta(days=2), time(12)))
        included.save(update_fields=['created_at'])
        excluded_category.created_at = included.created_at
        excluded_category.save(update_fields=['created_at'])
        excluded_date.created_at = timezone.make_aware(datetime.combine(today - timedelta(days=8), time(12)))
        excluded_date.save(update_fields=['created_at'])
        included.categories.add(category)

        request = RequestFactory().get('/tasks/', {
            'view': 'open',
            'created_after': (today - timedelta(days=3)).isoformat(),
            'tag_filter': '1',
            'category': str(category.pk),
        })
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        with patch('tasks.views.reverse', return_value='/tasks/'), patch(
            'tasks.views.render', side_effect=lambda request, template, context: context,
        ):
            response = index.__wrapped__(request)

        self.assertEqual([task.pk for task in response['tasks']], [included.pk])

    def test_created_date_presets_filter_month_and_year_and_expand_custom(self):
        today = timezone.localdate()
        this_month = Task.objects.create(title='This month')
        previous_month = Task.objects.create(title='Previous month')
        previous_year = Task.objects.create(title='Previous year')
        Task.objects.filter(pk=this_month.pk).update(
            created_at=timezone.make_aware(datetime.combine(today, time(12))),
        )
        Task.objects.filter(pk=previous_month.pk).update(
            created_at=timezone.make_aware(datetime.combine(today.replace(day=1) - timedelta(days=1), time(12))),
        )
        Task.objects.filter(pk=previous_year.pk).update(
            created_at=timezone.make_aware(datetime.combine(today.replace(year=today.year - 1), time(12))),
        )

        def context_for(query):
            request = RequestFactory().get('/tasks/', query)
            request.user = SimpleNamespace(is_active=True, is_staff=True)
            with patch('tasks.views.reverse', return_value='/tasks/'), patch(
                'tasks.views.render', side_effect=lambda request, template, context: context,
            ):
                return index.__wrapped__(request)

        month_context = context_for({'date_range': 'this_month'})
        self.assertEqual([task.pk for task in month_context['tasks']], [this_month.pk])
        self.assertEqual(month_context['date_range'], 'this_month')

        year_context = context_for({'date_range': 'this_year'})
        self.assertCountEqual(
            [task.pk for task in year_context['tasks']],
            [this_month.pk, previous_month.pk],
        )

        custom_context = context_for({'date_range': 'custom'})
        self.assertTrue(custom_context['filters_open'])
        self.assertEqual(custom_context['created_after'], '')

    def test_index_sorts_tasks_by_title_and_priority(self):
        zulu = Task.objects.create(title='Zulu task', priority=Task.Priority.HIGHEST)
        alpha = Task.objects.create(title='Alpha task', priority=Task.Priority.LOWEST)
        middle = Task.objects.create(title='Middle task', priority=Task.Priority.MEDIUM)

        def task_ids(sort_by, direction='asc'):
            request = RequestFactory().get('/tasks/', {
                'view': 'open',
                'sort_by': sort_by,
                'sort_direction': direction,
            })
            request.user = SimpleNamespace(is_active=True, is_staff=True)
            with patch('tasks.views.reverse', return_value='/tasks/'), patch(
                'tasks.views.render', side_effect=lambda request, template, context: context,
            ):
                context = index.__wrapped__(request)
            return [task.pk for task in context['tasks']]

        self.assertEqual(task_ids('title'), [alpha.pk, middle.pk, zulu.pk])
        self.assertEqual(task_ids('title', 'desc'), [zulu.pk, middle.pk, alpha.pk])
        self.assertEqual(task_ids('priority'), [zulu.pk, middle.pk, alpha.pk])

    def test_index_filter_can_match_multiple_tags(self):
        home = Category.objects.create(name='Home')
        work = Category.objects.create(name='Work')
        Category.objects.create(name='Other')
        home_task = Task.objects.create(title='Home task')
        work_task = Task.objects.create(title='Work task')
        both_task = Task.objects.create(title='Both tags')
        Task.objects.create(title='No tags')
        home_task.categories.add(home)
        work_task.categories.add(work)
        both_task.categories.add(home, work)

        request = RequestFactory().get('/tasks/', {
            'view': 'open',
            'tag_filter': '1',
            'category': [str(home.pk), str(work.pk)],
        })
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        with patch('tasks.views.reverse', return_value='/tasks/'), patch(
            'tasks.views.render', side_effect=lambda request, template, context: context,
        ):
            context = index.__wrapped__(request)

        self.assertCountEqual(
            [task.pk for task in context['tasks']],
            [home_task.pk, work_task.pk, both_task.pk],
        )
        self.assertEqual(context['selected_categories'], [str(home.pk), str(work.pk)])
        self.assertIn('category={}&category={}'.format(home.pk, work.pk), context['open_url'])

    def test_all_tags_are_selected_by_default_without_filtering_untagged_tasks(self):
        home = Category.objects.create(name='Home')
        work = Category.objects.create(name='Work')
        tagged = Task.objects.create(title='Tagged task')
        untagged = Task.objects.create(title='Untagged task')
        tagged.categories.add(home)
        request = RequestFactory().get('/tasks/', {'view': 'open'})
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        with patch('tasks.views.reverse', return_value='/tasks/'), patch(
            'tasks.views.render', side_effect=lambda request, template, context: context,
        ):
            context = index.__wrapped__(request)

        self.assertCountEqual([task.pk for task in context['tasks']], [tagged.pk, untagged.pk])
        self.assertEqual(context['selected_categories'], [str(home.pk), str(work.pk)])
        self.assertFalse(context['tag_filter_active'])

    def test_index_uses_preference_when_no_view_is_specified(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        preferences.default_view = TasksPreference.DefaultView.TODAY
        preferences.save(update_fields=['default_view'])
        request = RequestFactory().get('/tasks/')
        request.user = SimpleNamespace(is_active=True, is_staff=True)
        with patch('tasks.views.reverse', return_value='/tasks/'), patch(
            'tasks.views.render', side_effect=lambda request, template, context: context,
        ):
            context = index.__wrapped__(request)
        self.assertEqual(context['view_name'], TasksPreference.DefaultView.TODAY)

    def test_today_and_upcoming_views_use_local_due_dates(self):
        today = timezone.localdate()
        overdue = Task.objects.create(
            title='Overdue task',
            due_at=timezone.make_aware(datetime.combine(today - timedelta(days=1), time(9))),
        )
        due_today = Task.objects.create(
            title='Due today',
            due_at=timezone.make_aware(datetime.combine(today, time(9))),
        )
        upcoming = Task.objects.create(
            title='Upcoming task',
            due_at=timezone.make_aware(datetime.combine(today + timedelta(days=2), time(9))),
        )
        Task.objects.create(title='No due date')
        Task.objects.create(title='Subtask', parent=due_today)
        Task.objects.create(
            title='Completed today',
            completed=True,
            due_at=timezone.make_aware(datetime.combine(today, time(11))),
        )
        Task.objects.create(
            title='Cancelled today',
            cancelled_at=timezone.now(),
            due_at=timezone.make_aware(datetime.combine(today, time(12))),
        )

        self.assertEqual(
            {task.pk for task in self.tasks_for_view('today')},
            {overdue.pk, due_today.pk},
        )
        self.assertEqual(
            [task.pk for task in self.tasks_for_view('upcoming')],
            [upcoming.pk],
        )

    def test_quick_create_sets_due_priority_tags_and_subtask_parent(self):
        category = Category.objects.create(name='Home')
        tomorrow = timezone.localdate() + timedelta(days=1)
        due_at = datetime.combine(tomorrow, time(9)).strftime('%Y-%m-%dT%H:%M')
        response = self.create_task({
            'title': 'Call dentist',
            'priority': '5',
            'due_at': due_at,
            'categories[]': [str(category.pk)],
        })

        self.assertEqual(response.status_code, 200)
        task = Task.objects.get(pk=json.loads(response.content)['id'])
        self.assertEqual(task.title, 'Call dentist')
        self.assertEqual(task.priority, Task.Priority.HIGHEST)
        self.assertEqual(timezone.localdate(task.due_at), tomorrow)
        self.assertEqual(list(task.categories.all()), [category])

        child_response = self.create_task({'title': 'Find phone number', 'parent_id': str(task.pk)})
        child = Task.objects.get(pk=json.loads(child_response.content)['id'])
        self.assertEqual(child.parent_id, task.pk)
        self.assertEqual(self.create_task({
            'title': 'Nested child',
            'parent_id': str(child.pk),
        }).status_code, 400)
        self.assertEqual(self.update_task(task, 'completed', 'true').status_code, 200)
        self.assertEqual(self.update_task(task, 'archived', 'true').status_code, 200)
        self.assertEqual(self.update_task(task, 'delete', 'true').status_code, 200)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertFalse(Task.objects.filter(pk=child.pk).exists())

    def test_quick_create_uses_preferences_and_keeps_subtasks_non_recurring(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        preferences.default_priority = Task.Priority.HIGHEST
        preferences.default_recurrence = Task.Recurrence.WEEKLY
        preferences.save(update_fields=['default_priority', 'default_recurrence'])
        response = self.create_task({'title': 'Weekly review'})
        task = Task.objects.get(pk=json.loads(response.content)['id'])
        self.assertEqual(task.priority, Task.Priority.HIGHEST)
        self.assertEqual(task.recurrence, Task.Recurrence.WEEKLY)

        child_response = self.create_task({'title': 'Review notes', 'parent_id': str(task.pk)})
        child = Task.objects.get(pk=json.loads(child_response.content)['id'])
        self.assertEqual(child.recurrence, Task.Recurrence.NONE)

    def test_recurring_completion_creates_one_successor_with_tags_and_steps(self):
        category = Category.objects.create(name='Work')
        task = Task.objects.create(
            title='Weekly report',
            notes='Use the latest figures',
            priority=Task.Priority.HIGH,
            recurrence=Task.Recurrence.DAILY,
            due_at=timezone.now() - timedelta(days=2),
        )
        task.categories.add(category)
        step = Task.objects.create(title='Gather figures', parent=task)
        step.categories.add(category)

        self.assertEqual(self.update_task(task, 'completed', 'true').status_code, 200)
        task.refresh_from_db()
        successor = Task.objects.get(recurrence_source=task)
        self.assertEqual(successor.title, task.title)
        self.assertEqual(successor.notes, task.notes)
        self.assertEqual(successor.priority, task.priority)
        self.assertEqual(successor.recurrence, Task.Recurrence.DAILY)
        self.assertEqual(list(successor.categories.all()), [category])
        self.assertGreater(successor.due_at, task.completed_at)
        copied_step = successor.subtasks.get()
        self.assertEqual(copied_step.title, step.title)
        self.assertFalse(copied_step.completed)
        self.assertEqual(list(copied_step.categories.all()), [category])

        self.assertEqual(self.update_task(task, 'completed', 'false').status_code, 200)
        self.assertEqual(self.update_task(task, 'completed', 'true').status_code, 200)
        self.assertEqual(Task.objects.filter(recurrence_source=task).count(), 1)

    def test_adding_recurrence_to_completed_task_creates_next_occurrence(self):
        task = Task.objects.create(title='Completed routine', completed=True)
        response = self.update_task(task, 'recurrence', Task.Recurrence.WEEKLY)
        successor = Task.objects.get(recurrence_source=task)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(successor.recurrence, Task.Recurrence.WEEKLY)
        self.assertGreater(successor.due_at, task.completed_at)

    def test_undoing_recurring_completion_removes_its_new_successor(self):
        task = Task.objects.create(
            title='Recurring task',
            recurrence=Task.Recurrence.DAILY,
            due_at=timezone.now(),
        )
        completion_response = self.update_task(task, 'completed', 'true')
        successor_id = json.loads(completion_response.content)['next_task_id']
        request = RequestFactory().post('/tasks/api/', {
            'field': 'undo_completion',
            'value': 'false',
            'successor_id': str(successor_id),
        })
        response = update.__wrapped__.__wrapped__(request, task.pk)

        task.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(task.completed)
        self.assertFalse(Task.objects.filter(pk=successor_id).exists())

    def test_monthly_recurrence_clamps_month_end(self):
        due_at = timezone.make_aware(datetime(2026, 1, 31, 9))
        task = Task.objects.create(
            title='Month end task',
            recurrence=Task.Recurrence.MONTHLY,
            due_at=due_at,
        )
        self.assertEqual(
            task.next_occurrence_due_at(),
            timezone.make_aware(datetime(2026, 2, 28, 9)),
        )
        successor = Task.objects.create(
            title=task.title,
            recurrence=Task.Recurrence.MONTHLY,
            recurrence_anchor_day=31,
            recurrence_source=task,
            due_at=timezone.make_aware(datetime(2026, 2, 28, 9)),
        )
        self.assertEqual(
            successor.next_occurrence_due_at(timezone.make_aware(datetime(2026, 2, 28, 10))),
            timezone.make_aware(datetime(2026, 3, 31, 9)),
        )

    def test_preferences_api_updates_task_defaults(self):
        request = RequestFactory().post('/tasks/api/preferences/', {
            'default_priority': str(Task.Priority.HIGHEST),
            'default_recurrence': Task.Recurrence.MONTHLY,
            'default_view': TasksPreference.DefaultView.TODAY,
            'show_quick_capture_hint': 'false',
            'show_task_age': 'false',
            'filters_expanded_by_default': 'true',
            'default_reminder_minutes': str(TasksPreference.ReminderLeadTime.ONE_DAY),
            'auto_archive_after': TasksPreference.AutoArchiveAfter.THREE_MONTHS,
            'show_archived_tab': 'false',
            'show_cancelled_tab': 'true',
            'theme': TasksPreference.Theme.DARK,
            'background_pattern': TasksPreference.BackgroundPattern.CHECKERBOARD,
        })
        response = update_preferences.__wrapped__.__wrapped__(request)
        settings = TasksPreference.objects.get(pk=1)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(settings.default_priority, Task.Priority.HIGHEST)
        self.assertEqual(settings.default_recurrence, Task.Recurrence.MONTHLY)
        self.assertEqual(settings.default_view, TasksPreference.DefaultView.TODAY)
        self.assertFalse(settings.show_quick_capture_hint)
        self.assertFalse(settings.show_task_age)
        self.assertTrue(settings.filters_expanded_by_default)
        self.assertEqual(settings.default_reminder_minutes, TasksPreference.ReminderLeadTime.ONE_DAY)
        self.assertEqual(settings.auto_archive_after, TasksPreference.AutoArchiveAfter.THREE_MONTHS)
        self.assertFalse(settings.show_archived_tab)
        self.assertTrue(settings.show_cancelled_tab)
        self.assertEqual(settings.theme, TasksPreference.Theme.DARK)
        self.assertEqual(settings.background_pattern, TasksPreference.BackgroundPattern.CHECKERBOARD)

    def test_custom_theme_seed_requires_six_digit_hex_value(self):
        request = RequestFactory().post('/tasks/api/themes/create/', {
            'name': 'Invalid seed',
            'color': 'green',
        })
        request.user = SimpleNamespace(pk=17, is_active=True, is_staff=True)
        request.session = {}
        response = create_theme.__wrapped__.__wrapped__(request)

        self.assertEqual(response.status_code, 400)

    def test_theme_palette_derives_accessible_colors_from_seed(self):
        for seed in ('#a9d85d', '#000000', '#ffffff', '#123456', '#ff00ff'):
            palette = build_theme_palette(seed)
            self.assertEqual(palette['light-chartreuse'], seed)
            for mode in ('light', 'dark'):
                accent = palette[f'{mode}-chartreuse']
                paper = palette[f'{mode}-paper']
                self.assertGreaterEqual(
                    _contrast(accent, palette[f'{mode}-accent-ink']),
                    4.5,
                )
                self.assertGreaterEqual(_contrast(paper, palette[f'{mode}-forest']), 4.5)
                self.assertGreaterEqual(_contrast(paper, palette[f'{mode}-capture-tag']), 4.5)
                self.assertGreaterEqual(_contrast(paper, palette[f'{mode}-capture-repeat']), 4.5)

    def test_custom_seed_produces_distinct_light_and_dark_surfaces(self):
        default_palette = build_theme_palette(DEFAULT_THEME_SEED)
        for seed in ('#e9c4bd', '#e3c8e1'):
            palette = build_theme_palette(seed)
            for mode in ('light', 'dark'):
                for surface in ('paper', 'paper-faint', 'surface'):
                    color = palette[f'{mode}-{surface}']
                    default_color = default_palette[f'{mode}-{surface}']
                    distance = sum(
                        abs(int(color[index:index + 2], 16) - int(default_color[index:index + 2], 16))
                        for index in (1, 3, 5)
                    )
                    self.assertGreaterEqual(distance, 6 if surface == 'surface' else 12)

    def test_custom_themes_are_owned_selectable_and_deletable(self):
        owner = SimpleNamespace(pk=17, is_active=True, is_staff=True)
        request = RequestFactory().post('/tasks/api/themes/create/', {
            'name': 'Deep Green',
            'color': '#135724',
        })
        request.user = owner
        request.session = {}
        with patch('tasks.views.reverse', return_value='/tasks/api/themes/1/delete/'):
            response = create_theme.__wrapped__.__wrapped__(request)

        self.assertEqual(response.status_code, 201)
        theme = TasksTheme.objects.get(name='Deep Green')
        self.assertEqual(theme.owner_id, '17')
        self.assertEqual(theme.seed_color, '#135724')
        self.assertEqual(request.session['tasks_active_theme'], theme.pk)

        select_request = RequestFactory().post('/tasks/api/preferences/', {'active_theme': str(theme.pk)})
        select_request.user = SimpleNamespace(pk=18, is_active=True, is_staff=True)
        select_request.session = {}
        rejected = update_preferences.__wrapped__.__wrapped__(select_request)
        self.assertEqual(rejected.status_code, 400)

        select_request.user = owner
        selected = update_preferences.__wrapped__.__wrapped__(select_request)
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(select_request.session['tasks_active_theme'], theme.pk)
        selected_data = json.loads(selected.content)
        self.assertEqual(selected_data['seed_color'], '#135724')
        self.assertEqual(selected_data['palette']['light-chartreuse'], '#135724')

        delete_request = RequestFactory().post('/tasks/api/themes/1/delete/')
        delete_request.user = owner
        delete_request.session = {'tasks_active_theme': theme.pk}
        deleted = delete_theme.__wrapped__.__wrapped__(delete_request, theme.pk)
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(TasksTheme.objects.filter(pk=theme.pk).exists())
        self.assertNotIn('tasks_active_theme', delete_request.session)
        self.assertEqual(json.loads(deleted.content)['seed_color'], DEFAULT_THEME_SEED)

    def test_notes_can_be_saved_and_are_length_limited(self):
        task = Task.objects.create(title='Task with notes')

        self.assertEqual(self.update_task(task, 'notes', 'Call after lunch').status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.notes, 'Call after lunch')
        self.assertEqual(self.update_task(task, 'notes', 'x' * 20001).status_code, 400)

    def test_terminal_tasks_remain_editable_and_archived_task_can_reopen(self):
        category = Category.objects.create(name='Personal')
        task = Task.objects.create(title='Finished task', completed=True)
        new_due_at = timezone.make_aware(datetime.combine(timezone.localdate() + timedelta(days=4), time(14)))
        new_completed_at = timezone.make_aware(datetime.combine(timezone.localdate() - timedelta(days=1), time(16)))

        self.assertEqual(self.update_task(task, 'title', 'Updated finished task').status_code, 200)
        self.assertEqual(self.update_task_categories(task, [category.pk]).status_code, 200)
        self.assertEqual(self.update_task(task, 'notes', 'Updated details').status_code, 200)
        self.assertEqual(
            self.update_task(task, 'due_at', new_due_at.strftime('%Y-%m-%dT%H:%M')).status_code,
            200,
        )
        self.assertEqual(
            self.update_task(task, 'completed_at', new_completed_at.strftime('%Y-%m-%dT%H:%M')).status_code,
            200,
        )
        self.assertEqual(self.update_task(task, 'archived', 'true').status_code, 200)
        child_response = self.create_task({'title': 'Step added while archived', 'parent_id': str(task.pk)})
        child = Task.objects.get(pk=json.loads(child_response.content)['id'])
        self.assertEqual(child.parent_id, task.pk)
        self.assertEqual(self.update_task(child, 'title', 'Renamed archived step').status_code, 200)
        self.assertEqual(self.update_task(child, 'delete', 'true').status_code, 200)
        self.assertFalse(Task.objects.filter(pk=child.pk).exists())
        self.assertEqual(self.update_task(task, 'title', 'Updated while archived').status_code, 200)
        self.assertEqual(self.update_task(task, 'notes', 'Archived notes').status_code, 200)
        self.assertEqual(self.update_task_categories(task, []).status_code, 200)

        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated while archived')
        self.assertEqual(task.notes, 'Archived notes')
        self.assertFalse(task.categories.exists())
        self.assertEqual(task.due_at, new_due_at)
        self.assertEqual(task.completed_at, new_completed_at)

        self.assertEqual(self.update_task(task, 'completed', 'false').status_code, 200)
        task.refresh_from_db()
        self.assertFalse(task.completed)
        self.assertIsNone(task.archived_at)
        self.assertIn(task, self.tasks_for_view('open'))

        self.assertEqual(self.update_task(task, 'cancelled', 'true').status_code, 200)
        self.assertEqual(self.update_task(task, 'title', 'Updated while cancelled').status_code, 200)
        self.assertEqual(self.update_task_categories(task, [category.pk]).status_code, 200)
        self.assertEqual(self.update_task(task, 'cancelled', 'false').status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated while cancelled')
        self.assertEqual(list(task.categories.all()), [category])

    def test_completion_timestamp_is_set_and_cleared(self):
        task = Task.objects.create(title='Toggle completion')
        original_start = task.created_at
        response = self.update_task(task, 'completed', 'true')
        task.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(task.completed)
        self.assertIsNotNone(task.completed_at)

        response = self.update_task(task, 'completed', 'false')
        task.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(task.completed)
        self.assertIsNone(task.completed_at)
        self.assertEqual(task.created_at, original_start)

    def test_reminder_requires_due_date_and_is_disabled_when_date_is_cleared(self):
        task = Task.objects.create(title='Reminder needs a due date')
        self.assertEqual(self.update_task(task, 'reminder_enabled', 'true').status_code, 400)

        due_at = timezone.now() + timedelta(days=1)
        self.assertEqual(
            self.update_task(task, 'due_at', due_at.strftime('%Y-%m-%dT%H:%M')).status_code,
            200,
        )
        self.assertEqual(self.update_task(task, 'reminder_enabled', 'true').status_code, 200)
        self.assertEqual(self.update_task(task, 'due_at', '').status_code, 200)
        task.refresh_from_db()
        self.assertFalse(task.reminder_enabled)

    def test_cancel_archive_restore_and_delete_lifecycle(self):
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        preferences.show_cancelled_tab = True
        preferences.save(update_fields=['show_cancelled_tab'])
        task = Task.objects.create(title='Lifecycle task')

        self.assertEqual(self.update_task(task, 'cancelled', 'true').status_code, 200)
        task.refresh_from_db()
        self.assertIsNotNone(task.cancelled_at)
        self.assertIn(task, self.tasks_for_view('cancelled'))
        self.assertNotIn(task, self.tasks_for_view('open'))

        self.assertEqual(self.update_task(task, 'cancelled', 'false').status_code, 200)
        task.refresh_from_db()
        self.assertIsNone(task.cancelled_at)

        self.assertEqual(self.update_task(task, 'completed', 'true').status_code, 200)
        self.assertIn(task, self.tasks_for_view('completed'))
        self.assertNotIn(task, self.tasks_for_view('open'))
        self.assertEqual(self.update_task(task, 'delete', 'true').status_code, 400)
        self.assertEqual(self.update_task(task, 'archived', 'true').status_code, 200)
        task.refresh_from_db()
        self.assertIsNotNone(task.archived_at)
        self.assertIn(task, self.tasks_for_view('archived'))
        self.assertNotIn(task, self.tasks_for_view('completed'))

        self.assertEqual(self.update_task(task, 'archived', 'false').status_code, 200)
        task.refresh_from_db()
        self.assertIsNone(task.archived_at)
        self.assertEqual(self.update_task(task, 'completed', 'false').status_code, 200)
        self.assertEqual(self.update_task(task, 'cancelled', 'true').status_code, 200)
        self.assertEqual(self.update_task(task, 'delete', 'true').status_code, 200)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())