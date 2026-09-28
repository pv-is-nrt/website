from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0075_alter_presentation_conference_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publication',
            old_name='issue_etc',
            new_name='issue',
        ),
        migrations.RenameField(
            model_name='presentation',
            old_name='issue_etc',
            new_name='issue',
        ),
        migrations.RenameField(
            model_name='publication',
            old_name='crossref_confirmed',
            new_name='information_confirmed',
        ),
        migrations.RenameField(
            model_name='presentation',
            old_name='crossref_confirmed',
            new_name='information_confirmed',
        ),
        migrations.AddField(
            model_name='publication',
            name='container_title',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='publication',
            name='volume',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='presentation',
            name='container_title',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='presentation',
            name='volume',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='publication',
            name='information_confirmed',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='publication',
            name='issue',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='information_confirmed',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='issue',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]