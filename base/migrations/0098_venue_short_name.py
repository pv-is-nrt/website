from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0097_skillcategory_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='venue',
            old_name='acronym',
            new_name='short_name',
        ),
    ]