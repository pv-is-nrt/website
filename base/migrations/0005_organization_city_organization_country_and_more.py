# Generated by Django 4.0 on 2022-01-17 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_rename_honorsandawards_honorandaward_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='organization',
            name='country',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='organization',
            name='state',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
