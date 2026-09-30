from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import CATEGORY_COLORS, Category, Task, TasksPreference


@override_settings(ROOT_URLCONF='tasks.test_urls')
class TaskViewsTests(TestCase):
    databases = {'default', 'tasks'}

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='task-admin', password='test-password', is_staff=True)

    def test_page_requires_staff_login(self):
        response = self.client.get(reverse('tasks:index'))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_quick_add_and_update_task(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('tasks:create'), {'title': 'Write report'})
        self.assertEqual(response.status_code, 200)
        task = Task.objects.get(pk=response.json()['id'])
        self.assertEqual(task._state.db, 'tasks')

        response = self.client.post(reverse('tasks:update', args=[task.pk]), {'field': 'priority', 'value': '5'})
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.priority, Task.Priority.HIGHEST)

    def test_task_can_have_multiple_managed_categories(self):
        self.client.force_login(self.user)
        task = Task.objects.create(title='Plan trip')
        home = Category.objects.create(name='Home')
        travel = Category.objects.create(name='Travel')

        response = self.client.post(
            reverse('tasks:update', args=[task.pk]),
            {'field': 'categories', 'value[]': [str(home.pk), str(travel.pk)]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertSetEqual(set(task.categories.values_list('name', flat=True)), {'Home', 'Travel'})

    def test_preferences_manage_categories_and_default_reminder_lead(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasks:preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/preferences.html')
        self.assertEqual(len(response.context['category_colors']), 20)

        response = self.client.post(reverse('tasks:create-category'), {'name': 'Research'})
        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(pk=response.json()['id'])
        self.assertEqual(category.name, 'Research')

        response = self.client.post(
            reverse('tasks:update-category', args=[category.pk]),
            {'color': CATEGORY_COLORS[0][0]},
        )
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.color, CATEGORY_COLORS[0][0])

        response = self.client.post(
            reverse('tasks:update-category', args=[category.pk]),
            {'color': '#123456'},
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            reverse('tasks:update-preferences'),
            {'default_reminder_minutes': str(TasksPreference.ReminderLeadTime.ONE_DAY)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TasksPreference.objects.get(pk=1).default_reminder_minutes, 1440)

    def test_staff_page_uses_the_standalone_tasks_template(self):
        self.client.force_login(self.user)
        task = Task.objects.create(title='Review notes')
        home = Category.objects.create(name='Home')
        task.categories.add(home)
        completed = Task.objects.create(title='Old task', completed=True)

        response = self.client.get(reverse('tasks:index'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/index.html')
        self.assertContains(response, 'Review notes')
        self.assertContains(response, 'category-chip')
        self.assertContains(response, home.color)
        html = response.content.decode()
        completed_row = html.split(f'data-task-id="{completed.pk}"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('priority-select', completed_row)
        self.assertNotIn('due-picker', completed_row)
        self.assertNotIn('reminder-toggle', completed_row)
        self.assertNotIn('text-decoration: line-through', html)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        EMAIL_HOST_USER='sender@example.com',
        TASKS_REMINDER_EMAIL='recipient@example.com',
    )
    def test_reminder_command_emails_once_and_marks_task_sent(self):
        task = Task.objects.create(
            title='Submit report',
            due_at=timezone.now() + timedelta(minutes=30),
            reminder_enabled=True,
        )

        call_command('send_task_reminders')
        task.refresh_from_db()

        self.assertTrue(task.reminder_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['recipient@example.com'])
        call_command('send_task_reminders')
        self.assertEqual(len(mail.outbox), 1)

    def test_non_staff_cannot_add_task(self):
        user = get_user_model().objects.create_user(username='regular-user', password='test-password')
        self.client.force_login(user)
        response = self.client.post(reverse('tasks:create'), {'title': 'Private task'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.exists())