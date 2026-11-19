from django.db import migrations, models


def migrate_funded_status(apps, schema_editor):
    Proposal = apps.get_model('base', 'Proposal')
    Proposal.objects.using(schema_editor.connection.alias).filter(
        status='funded',
    ).update(status='awarded')


def reverse_awarded_status(apps, schema_editor):
    Proposal = apps.get_model('base', 'Proposal')
    Proposal.objects.using(schema_editor.connection.alias).filter(
        status='awarded',
    ).update(status='funded')


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0101_proposal_fields_and_statuses'),
    ]

    operations = [
        migrations.RunPython(migrate_funded_status, reverse_awarded_status),
        migrations.AlterField(
            model_name='proposal',
            name='amount',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='proposal',
            name='status',
            field=models.CharField(
                choices=[
                    ('awarded', 'Awarded'),
                    ('pending', 'Pending'),
                    ('not funded', 'Not funded'),
                ],
                max_length=200,
            ),
        ),
    ]
