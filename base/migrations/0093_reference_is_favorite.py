from django.db import migrations, models


def mark_existing_references_as_favorite(apps, schema_editor):
    Reference = apps.get_model('base', 'Reference')
    Reference.objects.using(schema_editor.connection.alias).update(is_favorite=True)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0092_remove_skillset'),
    ]

    operations = [
        migrations.AddField(
            model_name='reference',
            name='is_favorite',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(mark_existing_references_as_favorite),
    ]