# Generated by Django 4.0 on 2022-02-24 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0031_basicinformation_resume_tagline'),
    ]

    operations = [
        migrations.RenameField(
            model_name='basicinformation',
            old_name='personal_statement',
            new_name='cv_statement',
        ),
        migrations.AddField(
            model_name='basicinformation',
            name='resume_statement',
            field=models.TextField(blank=True),
        ),
    ]
