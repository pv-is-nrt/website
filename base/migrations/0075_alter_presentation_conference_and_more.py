from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0074_publication_presentation_crossref_confirmed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='presentation',
            name='conference',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='presentation',
            name='speaker_index',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='authors',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='publication',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publication',
            name='doi',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='publication',
            name='featured',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='publication',
            name='publisher',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='publication',
            name='title',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='publication',
            name='status',
            field=models.CharField(blank=True, choices=[('under review / submitted', 'under review / submitted'), ('submitting next', 'submitting next'), ('published', 'published'), ('in progress', 'in progress'), ('preprint', 'preprint')], default='in progress', max_length=200),
        ),
    ]