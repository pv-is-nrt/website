# Generated by Django 4.0 on 2022-02-26 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0033_rename_resume_statement_basicinformation_personal_statement_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillset',
            name='score',
            field=models.PositiveSmallIntegerField(blank=True, default=100),
            preserve_default=False,
        ),
    ]
