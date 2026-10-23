import re

from django.db import migrations


ALIASES = {
    'cnns': 'convolutional neural networks',
    'svms': 'support vector machines',
    'gnns': 'graph neural networks',
    'coatingformulations': 'chemical formulations',
    'silanechemistry': 'silanes & silicones',
    'itc': 'isothermal titration calorimetry',
    'tensorflow': 'tensorflow & pytorch',
}

NEW_SKILLS = {
    'gans': ('generative adversarial networks', 'GANs', 'Machine Learning'),
    'networkvisualization': ('network visualization', '', 'Machine Learning'),
    'statisticalprogramming': ('statistical programming', '', 'Machine Learning'),
    'molecularparsing': ('molecular parsing', '', 'Machine Learning'),
    'javascript': ('JavaScript', '', 'Computer languages'),
    'slotdiecoating': ('slot-die coating', '', 'Industry'),
    'barcoating': ('bar coating', '', 'Industry'),
    'adhesivecoatings': ('adhesive coatings', '', 'Industry'),
    'sem': ('scanning electron microscopy', 'SEM', 'Lab Techniques'),
    'careercounselling': ('career counselling', '', 'Interpersonal'),
    'dei': ('DEI', '', 'Interpersonal'),
    'pillow': ('Pillow', '', 'Computational'),
    'tableau': ('Tableau', '', 'Computational'),
}


def normalize(value):
    return re.sub(r'[^a-z0-9]+', '', value.casefold())


def transfer_unmatched_skills(apps, schema_editor):
    Skillset = apps.get_model('base', 'Skillset')
    Skill = apps.get_model('base', 'Skill')
    SkillCategory = apps.get_model('base', 'SkillCategory')
    database = schema_editor.connection.alias

    skills = list(Skill.objects.using(database).all())
    existing = {
        normalize(value): skill
        for skill in skills
        for value in (skill.name, skill.short_name)
        if value
    }
    categories = {
        normalize(category.name): category
        for category in SkillCategory.objects.using(database).all()
    }
    through = Skill._meta.get_field('category').remote_field.through
    relation_fields = [field for field in through._meta.fields if field.many_to_one]
    skill_relation = next(field for field in relation_fields if field.remote_field.model == Skill)
    category_relation = next(field for field in relation_fields if field.remote_field.model == SkillCategory)

    for skillset in Skillset.objects.using(database).all().iterator():
        for entry in skillset.skills.split(', '):
            if '#' not in entry:
                raise RuntimeError('Cannot parse legacy skill entry: {}'.format(entry))
            raw_name, raw_score = entry.rsplit('#', 1)
            raw_name = raw_name.strip().strip('*')
            name = raw_name.split(' (', 1)[0].strip()
            key = normalize(name)
            if key in ALIASES:
                if normalize(ALIASES[key]) not in existing:
                    raise RuntimeError('Legacy skill alias has no normalized target: {}'.format(raw_name))
                continue
            if key in existing:
                continue
            if key not in NEW_SKILLS:
                raise RuntimeError('Legacy skill has no normalized mapping: {}'.format(raw_name))

            skill_name, short_name, category_name = NEW_SKILLS[key]
            category = categories.get(normalize(category_name))
            if category is None:
                raise RuntimeError('Normalized skill category does not exist: {}'.format(category_name))
            skill = Skill.objects.using(database).create(
                name=skill_name,
                short_name=short_name,
                score=int(raw_score.strip().strip('*')),
                start_year=2006,
            )
            through.objects.using(database).create(**{
                skill_relation.attname: skill.pk,
                category_relation.attname: category.pk,
            })
            existing[normalize(skill_name)] = skill
            if short_name:
                existing[normalize(short_name)] = skill


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0091_venue_publisher'),
    ]

    operations = [
        migrations.RunPython(transfer_unmatched_skills),
        migrations.DeleteModel(name='Skillset'),
    ]