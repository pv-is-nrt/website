# Generated by Django 4.0 on 2022-03-02 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0037_presentation_featured'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentoring',
            name='diversity_tags',
            field=models.CharField(blank=True, choices=[('women', 'women'), ('african-americans', 'african-americans'), ('internationals', 'internationals'), ('other minorities', 'other minorities'), ('none', 'none')], default='none', max_length=200),
        ),
    ]
