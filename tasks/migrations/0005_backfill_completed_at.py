from django.db import migrations
from django.utils import timezone


def backfill_completed_at(apps, schema_editor):
    Task = apps.get_model('tasks', 'Task')
    Task.objects.using(schema_editor.connection.alias).filter(
        completed=True,
        completed_at__isnull=True,
    ).update(completed_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_task_completed_at'),
    ]

    operations = [
        migrations.RunPython(backfill_completed_at, migrations.RunPython.noop),
    ]