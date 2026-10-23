from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0095_category_skill_text_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='articles_reviewed',
            field=models.PositiveIntegerField(default=1),
        ),
    ]