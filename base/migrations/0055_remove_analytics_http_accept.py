# Generated by Django 4.0 on 2022-04-12 06:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0054_analytics'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='analytics',
            name='http_accept',
        ),
    ]
