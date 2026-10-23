from django.db import migrations, models
import django.db.models.deletion


def reviews_to_venues(apps, schema_editor):
    Review = apps.get_model('base', 'Review')
    Venue = apps.get_model('base', 'Venue')
    database = schema_editor.connection.alias

    for review in Review.objects.using(database).all().iterator():
        name = review.publication.strip()
        venue = Venue.objects.using(database).filter(name__iexact=name).first()
        if venue is None:
            venue = Venue.objects.using(database).create(name=name)
        review.venue_id = venue.pk
        review.save(using=database, update_fields=('venue',))


def venues_to_reviews(apps, schema_editor):
    Review = apps.get_model('base', 'Review')
    database = schema_editor.connection.alias

    for review in Review.objects.using(database).select_related('venue').iterator():
        review.publication = review.venue.name
        review.save(using=database, update_fields=('publication',))


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0089_alter_venue_kind'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='venue',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reviews',
                to='base.venue',
            ),
        ),
        migrations.RunPython(reviews_to_venues, venues_to_reviews),
        migrations.RemoveField(
            model_name='review',
            name='publication',
        ),
        migrations.AlterField(
            model_name='review',
            name='venue',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reviews',
                to='base.venue',
            ),
        ),
    ]