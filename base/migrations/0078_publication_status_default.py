from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0077_normalize_publication_presentation_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publication',
            name='status',
            field=models.CharField(blank=True, choices=[('under review / submitted', 'under review / submitted'), ('submitting next', 'submitting next'), ('published', 'published'), ('in progress', 'in progress'), ('preprint', 'preprint')], default='published', max_length=200),
        ),
    ]