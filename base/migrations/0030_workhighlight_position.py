# Generated by Django 4.0 on 2022-02-07 04:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0029_alter_workhighlight_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='workhighlight',
            name='position',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
