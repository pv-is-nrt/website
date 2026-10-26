from django.db import migrations, models


def preserve_category_order(apps, schema_editor):
    SkillCategory = apps.get_model('base', 'SkillCategory')
    for position, category in enumerate(SkillCategory.objects.order_by('pk'), start=1):
        category.order = position * 10
        category.save(update_fields=['order'])


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0096_review_articles_reviewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='skillcategory',
            name='order',
            field=models.PositiveSmallIntegerField(default=100),
        ),
        migrations.RunPython(preserve_category_order, migrations.RunPython.noop),
    ]