# Generated by Django 4.0 on 2022-01-17 04:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_advising_experience_honorsandawards_leadership_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='HonorsAndAwards',
            new_name='HonorAndAward',
        ),
        migrations.RenameModel(
            old_name='Messages',
            new_name='Message',
        ),
        migrations.RenameModel(
            old_name='Organizations',
            new_name='Organization',
        ),
        migrations.RenameModel(
            old_name='Presentations',
            new_name='Presentation',
        ),
        migrations.RenameModel(
            old_name='Proposals',
            new_name='Proposal',
        ),
        migrations.RenameModel(
            old_name='Publications',
            new_name='Publication',
        ),
        migrations.RenameModel(
            old_name='Skills',
            new_name='Skill',
        ),
    ]
