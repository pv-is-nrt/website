from django.db import migrations


def promote_verified_authors(apps, schema_editor):
    Presentation = apps.get_model('base', 'Presentation')
    for presentation in Presentation.objects.exclude(authors_full='').iterator():
        presentation.authors = presentation.authors_full
        presentation.save(update_fields=['authors'])


def preserve_original_authors(apps, schema_editor):
    # The temporary verification field is removed after its values are promoted.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0082_presentation_authors_full'),
    ]

    operations = [
        migrations.RunPython(promote_verified_authors, preserve_original_authors),
        migrations.RemoveField(
            model_name='presentation',
            name='authors_full',
        ),
    ]
