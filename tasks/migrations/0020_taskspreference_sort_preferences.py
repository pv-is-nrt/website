from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0019_task_reminder_recipient_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskspreference',
            name='sort_preferences',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]