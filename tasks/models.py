from django.db import models


CATEGORY_COLORS = (
    ('#f2d6c2', 'Peach'),
    ('#f3dfb4', 'Gold'),
    ('#eee8b6', 'Butter'),
    ('#e4e8b8', 'Olive'),
    ('#d6e4b9', 'Moss'),
    ('#c5dfc5', 'Sage'),
    ('#bfe0d4', 'Mint'),
    ('#b9dedc', 'Teal'),
    ('#c0dfeb', 'Sky'),
    ('#c7d9eb', 'Blue'),
    ('#ccd0e8', 'Periwinkle'),
    ('#d7cae5', 'Lavender'),
    ('#e3c8e1', 'Lilac'),
    ('#edc9d4', 'Rose'),
    ('#e9c4bd', 'Terracotta'),
    ('#ded0bc', 'Stone'),
    ('#cad7cc', 'Eucalyptus'),
    ('#c6d6d9', 'Slate'),
    ('#e4d3a3', 'Mustard'),
    ('#dbd8bf', 'Khaki'),
)


class Task(models.Model):
    class Priority(models.IntegerChoices):
        LOWEST = 1, '1'
        LOW = 2, '2'
        MEDIUM = 3, '3'
        HIGH = 4, '4'
        HIGHEST = 5, '5'

    title = models.CharField(max_length=240)
    categories = models.ManyToManyField('Category', blank=True, related_name='tasks')
    priority = models.PositiveSmallIntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    due_at = models.DateTimeField(null=True, blank=True)
    reminder_enabled = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    color = models.CharField(max_length=7, choices=CATEGORY_COLORS, default='#c5dfc5')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class TasksPreference(models.Model):
    class ReminderLeadTime(models.IntegerChoices):
        FIFTEEN_MINUTES = 15, '15 minutes'
        THIRTY_MINUTES = 30, '30 minutes'
        ONE_HOUR = 60, '1 hour'
        TWO_HOURS = 120, '2 hours'
        SIX_HOURS = 360, '6 hours'
        TWELVE_HOURS = 720, '12 hours'
        ONE_DAY = 1440, '1 day'
        TWO_DAYS = 2880, '2 days'
        ONE_WEEK = 10080, '1 week'

    default_reminder_minutes = models.PositiveIntegerField(
        choices=ReminderLeadTime.choices,
        default=ReminderLeadTime.ONE_HOUR,
    )

    def __str__(self):
        return 'Task preferences'