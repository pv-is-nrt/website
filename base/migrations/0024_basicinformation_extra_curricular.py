# Generated by Django 4.0 on 2022-02-04 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0023_alter_publication_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='basicinformation',
            name='extra_curricular',
            field=models.TextField(blank=True),
        ),
    ]
