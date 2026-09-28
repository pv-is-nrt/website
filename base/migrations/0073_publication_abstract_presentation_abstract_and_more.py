from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0072_delete_jobdescription'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='abstract',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='presentation',
            name='abstract',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='presentation',
            name='doi',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]