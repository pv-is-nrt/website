import calendar
from datetime import timedelta

from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


CATEGORY_PALETTE = (
    ('#eee8b6', '#746a1b', 'Butter'),
    ('#c5dfc5', '#296529', 'Sage'),
    ('#bfe0d4', '#296550', 'Mint'),
    ('#b9dedc', '#296562', 'Teal'),
    ('#c0dfeb', '#22586c', 'Sky'),
    ('#c7d9eb', '#264769', 'Blue'),
    ('#ccd0e8', '#293265', 'Periwinkle'),
    ('#d7cae5', '#462965', 'Lavender'),
    ('#e3c8e1', '#652961', 'Lilac'),
    ('#e9c4bd', '#6b2f24', 'Terracotta'),
    ('#ded0bc', '#654d29', 'Stone'),
    ('#cad7cc', '#296533', 'Eucalyptus'),
    ('#c6d6d9', '#295c65', 'Slate'),
    ('#edc9d4', '#6b243a', 'Rose'),
    ('#e4d3a3', '#6e5a20', 'Mustard'),
    ('#dbd8bf', '#655f29', 'Khaki'),
)


class Task(models.Model):
    class Priority(models.IntegerChoices):
        LOWEST = 1, '1'
        LOW = 2, '2'
        MEDIUM = 3, '3'
        HIGH = 4, '4'
        HIGHEST = 5, '5'

    class Recurrence(models.TextChoices):
        NONE = 'none', 'Does not repeat'
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    title = models.CharField(max_length=240)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subtasks',
    )
    notes = models.TextField(blank=True)
    categories = models.ManyToManyField('Category', blank=True, related_name='tasks')
    priority = models.PositiveSmallIntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    recurrence = models.CharField(max_length=8, choices=Recurrence.choices, default=Recurrence.NONE)
    recurrence_anchor_day = models.PositiveSmallIntegerField(null=True, blank=True)
    recurrence_source = models.OneToOneField(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='recurrence_successor',
    )
    due_at = models.DateTimeField(null=True, blank=True)
    reminder_enabled = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    reminder_recipient_email = models.EmailField(blank=True, default='')
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        completion_timestamp_changed = False
        recurrence_anchor_changed = False
        if self.completed and self.completed_at is None:
            self.completed_at = timezone.now()
            completion_timestamp_changed = True
        elif not self.completed and self.completed_at is not None:
            self.completed_at = None
            completion_timestamp_changed = True
        if self.recurrence != self.Recurrence.NONE and self.recurrence_anchor_day is None:
            recurrence_base = self.due_at or self.completed_at
            if recurrence_base:
                self.recurrence_anchor_day = recurrence_base.day
                recurrence_anchor_changed = True
        if kwargs.get('update_fields') is not None:
            update_fields = set(kwargs['update_fields'])
            if completion_timestamp_changed:
                update_fields.add('completed_at')
            if recurrence_anchor_changed:
                update_fields.add('recurrence_anchor_day')
            kwargs['update_fields'] = update_fields
        super().save(*args, **kwargs)

    @property
    def days_open(self):
        return max((timezone.localdate() - timezone.localdate(self.created_at)).days, 0)

    @property
    def days_to_complete(self):
        if not self.completed:
            return None
        completed_date = timezone.localdate(self.completed_at) if self.completed_at else timezone.localdate()
        return max((completed_date - timezone.localdate(self.created_at)).days, 0)

    @property
    def age_progress(self):
        age_days = self.days_open
        if self.completed:
            age_days = self.days_to_complete or 0
        return min(max(age_days, 0), 30) * 100 / 30

    def next_occurrence_due_at(self, completed_at=None):
        if self.recurrence == self.Recurrence.NONE:
            return None
        base = self.due_at or completed_at or timezone.now()
        anchor_day = self.recurrence_anchor_day or base.day

        def occurrence_after(periods):
            if self.recurrence == self.Recurrence.DAILY:
                return base + timedelta(days=periods)
            if self.recurrence == self.Recurrence.WEEKLY:
                return base + timedelta(weeks=periods)
            if self.recurrence == self.Recurrence.MONTHLY:
                month_index = base.month - 1 + periods
                year = base.year + month_index // 12
                month = month_index % 12 + 1
                day = min(anchor_day, calendar.monthrange(year, month)[1])
                return base.replace(year=year, month=month, day=day)
            year = base.year + periods
            day = min(anchor_day, calendar.monthrange(year, base.month)[1])
            return base.replace(year=year, day=day)

        periods = 1
        next_due_at = occurrence_after(periods)
        while completed_at and next_due_at <= completed_at:
            periods += 1
            next_due_at = occurrence_after(periods)
        return next_due_at


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    color = models.CharField(
        max_length=7,
        choices=tuple((light, label) for light, dark, label in CATEGORY_PALETTE),
        default='#c5dfc5',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    @property
    def dark_color(self):
        return next((dark for light, dark, _ in CATEGORY_PALETTE if light == self.color), self.color)


PRIORITY_ICON_PALETTE = (
    (Task.Priority.LOWEST, 'plane-takeoff', '#d7cae5', '#462965'),
    (Task.Priority.LOW, 'car', '#e9c4bd', '#6b2f24'),
    (Task.Priority.MEDIUM, 'rabbit', '#e4d3a3', '#6e5a20'),
    (Task.Priority.HIGH, 'turtle', '#b9dedc', '#296562'),
    (Task.Priority.HIGHEST, 'snail', '#c5dfc5', '#296529'),
)


class TasksPreference(models.Model):
    class DefaultView(models.TextChoices):
        OPEN = 'open', 'Open'
        TODAY = 'today', 'Today'
        UPCOMING = 'upcoming', 'Upcoming'

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
        ONE_MONTH = 43200, '1 month'

    class AutoArchiveAfter(models.TextChoices):
        ONE_WEEK = '1w', '1 week'
        TWO_WEEKS = '2w', '2 weeks'
        ONE_MONTH = '1m', '1 month'
        THREE_MONTHS = '3m', '3 months'
        SIX_MONTHS = '6m', '6 months'
        ONE_YEAR = '1y', '1 year'

    class Theme(models.TextChoices):
        AUTO = 'auto', 'Auto'
        LIGHT = 'light', 'Light'
        DARK = 'dark', 'Dark'

    class BackgroundPattern(models.TextChoices):
        NONE = 'none', 'None'
        GRID = 'grid', 'Fine grid'
        DOTS = 'dots', 'Dots'
        CHECKERBOARD = 'checkerboard', 'Checkerboard'

    class PriorityIconStyle(models.TextChoices):
        STROKE = 'stroke', 'Stroke'
        FILL = 'fill', 'Fill'

    default_reminder_minutes = models.PositiveIntegerField(
        choices=ReminderLeadTime.choices,
        default=ReminderLeadTime.ONE_HOUR,
    )
    daily_reminder_minutes = models.PositiveIntegerField(
        choices=ReminderLeadTime.choices,
        default=ReminderLeadTime.ONE_HOUR,
    )
    weekly_reminder_minutes = models.PositiveIntegerField(
        choices=ReminderLeadTime.choices,
        default=ReminderLeadTime.ONE_DAY,
    )
    monthly_reminder_minutes = models.PositiveIntegerField(
        choices=ReminderLeadTime.choices,
        default=ReminderLeadTime.ONE_WEEK,
    )
    yearly_reminder_minutes = models.PositiveIntegerField(
        choices=ReminderLeadTime.choices,
        default=ReminderLeadTime.ONE_MONTH,
    )
    default_priority = models.PositiveSmallIntegerField(
        choices=Task.Priority.choices,
        default=Task.Priority.MEDIUM,
    )
    default_recurrence = models.CharField(
        max_length=8,
        choices=Task.Recurrence.choices,
        default=Task.Recurrence.NONE,
    )
    default_view = models.CharField(
        max_length=8,
        choices=DefaultView.choices,
        default=DefaultView.OPEN,
    )
    show_quick_capture_hint = models.BooleanField(default=True)
    show_priority_numbers = models.BooleanField(default=True)
    priority_icon_style = models.CharField(
        max_length=6,
        choices=PriorityIconStyle.choices,
        default=PriorityIconStyle.STROKE,
    )
    show_task_age = models.BooleanField(default=True)
    filters_expanded_by_default = models.BooleanField(default=False)
    auto_archive_after = models.CharField(
        max_length=2,
        choices=AutoArchiveAfter.choices,
        default=AutoArchiveAfter.ONE_YEAR,
    )
    show_archived_tab = models.BooleanField(default=True)
    show_cancelled_tab = models.BooleanField(default=False)
    theme = models.CharField(max_length=5, choices=Theme.choices, default=Theme.AUTO)
    background_pattern = models.CharField(
        max_length=12,
        choices=BackgroundPattern.choices,
        default=BackgroundPattern.NONE,
    )

    def __str__(self):
        return 'Task preferences'


class TasksTheme(models.Model):
    owner_id = models.CharField(max_length=150, db_index=True)
    name = models.CharField(max_length=40)
    seed_color = models.CharField(max_length=7)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(Lower('name'), 'owner_id', name='tasks_theme_owner_name_ci_uniq'),
        ]

    def __str__(self):
        return self.name