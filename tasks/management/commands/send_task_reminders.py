from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from tasks.models import Task, TasksPreference


class Command(BaseCommand):
    help = 'Email reminders for tasks whose reminder time has arrived.'

    def handle(self, *args, **options):
        recipient = getattr(settings, 'TASKS_REMINDER_EMAIL', settings.EMAIL_HOST_USER)
        preferences, _ = TasksPreference.objects.get_or_create(pk=1)
        reminder_cutoff = timezone.now() + timedelta(minutes=preferences.default_reminder_minutes)
        due_tasks = Task.objects.filter(
            completed=False,
            reminder_enabled=True,
            reminder_sent=False,
            due_at__isnull=False,
            due_at__lte=reminder_cutoff,
        )
        sent = 0
        for task in due_tasks.iterator():
            result = send_mail(
                subject=f'Task reminder: {task.title}',
                message=f'Your task reminder is due now:\n\n{task.title}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[recipient],
                fail_silently=False,
            )
            if result:
                task.reminder_sent = True
                task.save(update_fields=['reminder_sent', 'updated_at'])
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} task reminder(s).'))