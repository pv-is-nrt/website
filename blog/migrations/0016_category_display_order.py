# Generated by Django 3.2.5 on 2022-12-10 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0015_alter_post_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='display_order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]