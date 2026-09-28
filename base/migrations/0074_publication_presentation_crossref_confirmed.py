from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0073_publication_abstract_presentation_abstract_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='publication',
            name='crossref_confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='presentation',
            name='crossref_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]