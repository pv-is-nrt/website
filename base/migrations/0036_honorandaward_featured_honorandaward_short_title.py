# Generated by Django 4.0 on 2022-02-27 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0035_skillset_category_full'),
    ]

    operations = [
        migrations.AddField(
            model_name='honorandaward',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='honorandaward',
            name='short_title',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
