# Generated by Django 4.0 on 2022-04-12 03:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0050_rename_email_in_log_message_email_in_success_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='email_in_success',
            field=models.BooleanField(blank=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='email_out_success',
            field=models.BooleanField(blank=True),
        ),
    ]
