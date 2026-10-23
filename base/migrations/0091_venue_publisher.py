from django.db import migrations, models


PUBLISHERS = (
    'MDPI',
    'Elsevier',
    'Sage',
    'AIP',
    'IOP',
    'ACS',
    'Wiley',
    'Microsoft',
)


def split_publisher_from_name(apps, schema_editor):
    Venue = apps.get_model('base', 'Venue')
    database = schema_editor.connection.alias

    for venue in Venue.objects.using(database).all().iterator():
        for publisher in PUBLISHERS:
            suffix = ' ({})'.format(publisher)
            if venue.name.endswith(suffix):
                venue.name = venue.name[:-len(suffix)]
                venue.publisher = publisher
                venue.save(using=database, update_fields=('name', 'publisher'))
                break


def restore_publisher_in_name(apps, schema_editor):
    Venue = apps.get_model('base', 'Venue')
    database = schema_editor.connection.alias

    for venue in Venue.objects.using(database).exclude(publisher='').iterator():
        venue.name = '{} ({})'.format(venue.name, venue.publisher)
        venue.publisher = ''
        venue.save(using=database, update_fields=('name', 'publisher'))


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0090_review_venue'),
    ]

    operations = [
        migrations.AddField(
            model_name='venue',
            name='publisher',
            field=models.CharField(blank=True, default='', max_length=200),
            preserve_default=False,
        ),
        migrations.RunPython(split_publisher_from_name, restore_publisher_in_name),
        migrations.AlterField(
            model_name='venue',
            name='publisher',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]