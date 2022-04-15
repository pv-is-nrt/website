# Generated by Django 3.2.5 on 2022-04-08 22:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0048_organization_google_maps_url'),
        ('blog', '0007_auto_20220408_1725'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base.organization'),
        ),
    ]
