# Generated by Django 3.2.5 on 2022-03-18 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0044_publicationtag'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentation',
            name='tags',
            field=models.ManyToManyField(blank=True, to='base.PublicationTag'),
        ),
        migrations.AddField(
            model_name='publication',
            name='tags',
            field=models.ManyToManyField(blank=True, to='base.PublicationTag'),
        ),
    ]
