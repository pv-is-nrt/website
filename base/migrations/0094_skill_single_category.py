from django.db import migrations, models
import django.db.models.deletion


def assign_single_skill_categories(apps, schema_editor):
    Skill = apps.get_model('base', 'Skill')
    SkillCategory = apps.get_model('base', 'SkillCategory')
    database = schema_editor.connection.alias
    selected_categories = {
        'MATLAB': 'Computer languages',
        'thermal & UV curing': 'Industry',
    }

    through = Skill._meta.get_field('category').remote_field.through
    relation_fields = [field for field in through._meta.fields if field.many_to_one]
    skill_relation = next(field for field in relation_fields if field.remote_field.model == Skill)
    category_relation = next(field for field in relation_fields if field.remote_field.model == SkillCategory)

    for skill in Skill.objects.using(database).all().iterator():
        category_ids = list(through.objects.using(database).filter(
            **{skill_relation.attname: skill.pk}
        ).values_list(category_relation.attname, flat=True))

        selected_name = selected_categories.get(skill.name)
        if selected_name:
            matches = list(SkillCategory.objects.using(database).filter(
                name=selected_name
            ).values_list('pk', flat=True))
            if len(matches) != 1 or matches[0] not in category_ids:
                raise RuntimeError(
                    'Selected category is missing from skill assignments: {}'.format(skill.name)
                )
            category_id = matches[0]
        elif len(category_ids) == 1:
            category_id = category_ids[0]
        else:
            raise RuntimeError(
                'Skill must have exactly one category before migration: {}'.format(skill.name)
            )

        Skill.objects.using(database).filter(pk=skill.pk).update(
            primary_category_id=category_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0093_reference_is_favorite'),
    ]

    operations = [
        migrations.AddField(
            model_name='skill',
            name='primary_category',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='base.skillcategory',
            ),
        ),
        migrations.RunPython(assign_single_skill_categories),
        migrations.RemoveField(
            model_name='skill',
            name='category',
        ),
        migrations.RenameField(
            model_name='skill',
            old_name='primary_category',
            new_name='category',
        ),
        migrations.AlterField(
            model_name='skill',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='base.skillcategory',
            ),
        ),
    ]