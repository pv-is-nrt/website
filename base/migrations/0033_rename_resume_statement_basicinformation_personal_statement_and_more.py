# Generated by Django 4.0 on 2022-02-25 07:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0032_rename_personal_statement_basicinformation_cv_statement_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='basicinformation',
            old_name='resume_statement',
            new_name='personal_statement',
        ),
        migrations.RemoveField(
            model_name='basicinformation',
            name='cv_statement',
        ),
    ]
