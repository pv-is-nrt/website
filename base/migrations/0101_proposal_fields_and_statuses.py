from django.db import migrations, models


def migrate_awarded_status(apps, schema_editor):
    Proposal = apps.get_model('base', 'Proposal')
    Proposal.objects.using(schema_editor.connection.alias).filter(
        status='awarded',
    ).update(status='funded')


def reverse_funded_status(apps, schema_editor):
    Proposal = apps.get_model('base', 'Proposal')
    Proposal.objects.using(schema_editor.connection.alias).filter(
        status='funded',
    ).update(status='awarded')


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0100_alter_publicationtype_name'),
    ]

    operations = [
        migrations.RunPython(migrate_awarded_status, reverse_funded_status),
        migrations.AddField(
            model_name='proposal',
            name='link',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='award_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='proposal',
            name='amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='Amount (USD)',
            ),
        ),
        migrations.AddField(
            model_name='proposal',
            name='duration',
            field=models.CharField(
                blank=True,
                help_text='For example, 3 years',
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name='proposal',
            name='status',
            field=models.CharField(
                choices=[
                    ('funded', 'Funded'),
                    ('pending', 'Pending'),
                    ('not funded', 'Not funded'),
                ],
                max_length=200,
            ),
        ),
    ]
