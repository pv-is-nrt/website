# Generated by Django 4.0 on 2022-02-27 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0034_skillset_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillset',
            name='category_full',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
