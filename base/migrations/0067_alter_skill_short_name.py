# Generated by Django 3.2.5 on 2023-02-08 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0066_skill_skillcategory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skill',
            name='short_name',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
