# Generated by Django 4.0.3 on 2023-05-31 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0070_jobdescription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobdescription',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
