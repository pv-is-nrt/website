# Generated by Django 4.0 on 2022-01-21 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_alter_advising_end_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mentoring',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='teaching',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
