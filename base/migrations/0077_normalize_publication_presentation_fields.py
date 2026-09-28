from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0076_rename_issue_and_information_confirmed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='title',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='publication',
            name='authors',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='publication',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='doi',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='conference',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='date',
            field=models.DateField(),
        ),
        migrations.AddField(
            model_name='publication',
            name='pages',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='publication',
            name='article_number',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='publication',
            name='publication_type',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='presentation',
            name='pages',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='presentation',
            name='article_number',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='presentation',
            name='publication_type',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]