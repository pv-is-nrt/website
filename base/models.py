from datetime import date as datetime_date

from django.core.exceptions import ValidationError
from django.db import models
 
#    Organizations
# ---------------------------------------------------------------------------- #

class Organization(models.Model):
    short_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    google_maps_url = models.URLField(blank=True)

    def __str__(self):
        return self.full_name + ' (' + self.short_name + ')'


#    Diversity Tags
# ---------------------------------------------------------------------------- #

class DiversityTag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


#    Publication tags
# ---------------------------------------------------------------------------- #

class PublicationTag(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


PUBLICATION_TYPE_NAMES = (
    'proceedings-article',
    'journal-article',
    'preprint',
    'other',
)


class PublicationType(models.Model):
    name = models.CharField(max_length=100, unique=True, default='journal-article')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BasicInformation(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    birth_date = models.DateField()
    notification_email = models.EmailField()
    contact_email = models.EmailField(blank=True)
    personal_email = models.EmailField(blank=True)
    work_email = models.EmailField(blank=True)
    country_phone_code = models.PositiveSmallIntegerField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=20)
    website_tagline = models.CharField(max_length=100, blank=True)
    cv_tagline = models.CharField(max_length=100, blank=True)
    resume_tagline = models.CharField(max_length=100, blank=True)
    personal_statement = models.TextField(blank=True)
    resume_statement = models.TextField(blank=True)
    cv_statement = models.TextField(blank=True)
    website_statement = models.TextField(blank=True)
    extra_curricular = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    scholar_url = models.URLField(blank=True)
    researchgate_url = models.URLField(blank=True)
    orcid_url = models.URLField(blank=True)
    publons_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    snapchat_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    medium_url = models.URLField(blank=True)
    towardsdatascience_url = models.URLField(blank=True)
    
    # return a string representation of the object
    def __str__(self):
        return self.first_name + " " + self.last_name


class GoogleScholar(models.Model):
    citations = models.PositiveBigIntegerField(null=True, blank=True)
    h_index = models.PositiveIntegerField(null=True, blank=True)
    i10_index = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'google_scholar'

    def __str__(self):
        return 'Google Scholar profile metrics'


#    Education
# ---------------------------------------------------------------------------- #

class Education(models.Model):
    
    # define the fields
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    degree = models.CharField(max_length=200)
    major = models.CharField(max_length=200)
    minor = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    thesis = models.CharField(max_length=200, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=1)
    gpa_total = models.DecimalField(max_digits=3, decimal_places=1)
    description = models.TextField(blank=True)

    # return a string representation of the object
    def __str__(self):
        return self.organization.short_name + " (" + self.degree + ")"


#    Work experience
# ---------------------------------------------------------------------------- #

class Experience(models.Model):

    # define the fields
    position = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    supervisor = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    short_description = models.TextField(blank=True)

    # return a string representation of the object
    def __str__(self):
        return self.position + " at " + self.organization.short_name


#    Messages
# ---------------------------------------------------------------------------- #

class Message(models.Model):

    # define the fields
    hidden_field = models.CharField(max_length=200, blank=True) # anti-spam measure
    senders_name = models.CharField(max_length=200)
    senders_email = models.EmailField()
    message = models.TextField()
    # the following two fields hold the return int 1 (success) or 0 (failure) for the send_mail function
    email_in_success = models.BooleanField(null=True)
    email_out_success = models.BooleanField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True) # adds a timestamp

    # return a string representation of the object
    def __str__(self):
        return self.senders_name


class Venue(models.Model):
    KIND_CHOICES = [
        ('journal', 'Journal'),
        ('conference', 'Conference'),
        ('conference_proceeding', 'Conference proceeding'),
        ('conference_workshop', 'Conference workshop'),
        ('book_series', 'Book series'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=500, unique=True)
    publisher = models.CharField(max_length=200, blank=True)
    kind = models.CharField(max_length=21, choices=KIND_CHOICES, default='other')
    issn = models.CharField(max_length=20, blank=True)
    eissn = models.CharField(max_length=20, blank=True)
    short_name = models.CharField(max_length=50, blank=True)
    url = models.URLField(blank=True)

    def __str__(self):
        return self.name

    @property
    def latest_metrics(self):
        latest = {}
        for metric in self.metrics.all():
            latest.setdefault(metric.metric_type, metric)
        return list(latest.values())

    @property
    def cv_metrics(self):
        return [
            metric for metric in self.latest_metrics
            if (metric.metric_type == 'impact_factor' and metric.value > 4)
            or (metric.metric_type == 'acceptance_rate' and metric.value < 40)
        ]


class VenueMetric(models.Model):
    METRIC_TYPES = [
        ('impact_factor', 'Impact factor'),
        ('acceptance_rate', 'Acceptance rate'),
    ]

    venue = models.ForeignKey(Venue, related_name='metrics', on_delete=models.CASCADE)
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    year = models.PositiveSmallIntegerField()
    value = models.DecimalField(max_digits=10, decimal_places=3)
    accepted_count = models.PositiveIntegerField(null=True, blank=True)
    submission_count = models.PositiveIntegerField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    verified_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ('metric_type', '-year')
        constraints = [
            models.UniqueConstraint(
                fields=('venue', 'metric_type', 'year'),
                name='unique_venue_metric_year',
            ),
        ]

    def __str__(self):
        return '{} {} ({})'.format(self.venue, self.get_metric_type_display(), self.year)

    @property
    def display_value(self):
        return format(self.value.normalize(), 'f')


#    Publications
# ---------------------------------------------------------------------------- #

class Publication(models.Model):

    # define the fields
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500)
    publisher = models.CharField(max_length=200, blank=True)
    venue = models.ForeignKey(Venue, null=True, blank=True, related_name='publications', on_delete=models.SET_NULL)
    volume = models.CharField(max_length=100, blank=True)
    issue = models.CharField(max_length=100, blank=True)
    date = models.DateField(null=True, blank=True)
    doi = models.CharField(max_length=200, blank=True)
    pages = models.CharField(max_length=100, blank=True)
    article_number = models.CharField(max_length=100, blank=True)
    publication_types = models.ManyToManyField(PublicationType, blank=True)
    abstract = models.TextField(blank=True)
    keywords = models.TextField(blank=True)
    information_confirmed = models.BooleanField(default=False, blank=True)
    link = models.URLField(blank=True)
    featured = models.BooleanField(default=False, blank=True)
    citations = models.CharField(max_length=10, blank=True)
    citations_updated_on = models.DateField(null=True, blank=True)
    crossref_updated_on = models.DateField(default=datetime_date(2026, 9, 30))
    # set on the preprint; the final publication reaches it through `preprint`
    published_version = models.OneToOneField('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='preprint', limit_choices_to=~models.Q(publication_types__name='preprint'))
    status = models.CharField(max_length=200, choices=[("under review / submitted", "under review / submitted"), ("submitting next", "submitting next"), ("published", "published"), ("in progress", "in progress")], default="published", blank=True)
    comment = models.CharField(max_length=200, blank=True)
    tags = models.ManyToManyField(PublicationTag, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    # return a string representation of the object
    def __str__(self):
        # return date year and title
        return (str(self.date.year) if self.date else "Undated") + " - " + self.title
    def clean(self):
        if self.published_version_id and self.published_version_id == self.pk:
            raise ValidationError({'published_version': 'A publication cannot be its own published version.'})
    def is_conference_proceeding(self):
        return self.publication_types.filter(name='proceedings-article').exists()
    def is_preprint(self):
        return self.publication_types.filter(name='preprint').exists()
    # return authors as a list of authors
    def authors_list(self):
        return self.authors.split(", ")
    def authors_list_short(self):
        if len(self.authors_list()) > 5:
            if 'Prateek Verma' in self.authors_list()[0:5]:
                return self.authors_list()[0:5] + ["et al."]
            else:
                return self.authors_list()[0:3] + ["...", "Prateek Verma", "et al."]
        else:
            return self.authors_list()
    def authors_list_very_short(self):
        if len(self.authors_list()) > 3:
            if 'Prateek Verma' in self.authors_list()[0:3]:
                return self.authors_list()[0:3] + ["et al."]
            else:
                return self.authors_list()[0:2] + ["...", "Prateek Verma", "et al."]
        else:
            return self.authors_list()


#    Presentations
# ---------------------------------------------------------------------------- #

class Presentation(models.Model):
    # define the fields
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500)
    speaker_index = models.PositiveSmallIntegerField(null=True, blank=True)
    conference = models.CharField(max_length=200)
    date = models.DateField()
    doi = models.CharField(max_length=200, blank=True)
    abstract = models.TextField(blank=True)
    information_confirmed = models.BooleanField(default=False, blank=True)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200)
    link = models.URLField(blank=True)
    featured = models.BooleanField(default=False)
    citations = models.CharField(max_length=10, blank=True)
    container_title = models.CharField(max_length=500, blank=True)
    volume = models.CharField(max_length=100, blank=True)
    issue = models.CharField(max_length=100, blank=True)
    pages = models.CharField(max_length=100, blank=True)
    article_number = models.CharField(max_length=100, blank=True)
    publication_type = models.CharField(max_length=100, blank=True)
    comment = models.CharField(max_length=200, blank=True)
    tags = models.ManyToManyField(PublicationTag, blank=True)

    # return a string representation of the object
    def __str__(self):
        # return date year and title
        return str(self.date.year) + " - " + self.title
    # return authors as a list of authors
    def authors_list(self):
        return self.authors.split(", ")
    def authors_list_short(self):
        if len(self.authors_list()) > 5:
            return self.authors_list()[0:5] + ["et al."]
        else:
            return self.authors_list()
    def authors_list_very_short(self):
        if len(self.authors_list()) > 3:
            if 'Prateek Verma' in self.authors_list()[0:3]:
                return self.authors_list()[0:3] + ["et al."]
            else:
                return self.authors_list()[0:2] + ["...", "Prateek Verma", "et al."]
        else:
            return self.authors_list()


#    Proposals
# ---------------------------------------------------------------------------- #

class Proposal(models.Model):

    # define the fields
    title = models.CharField(max_length=500)
    pi = models.CharField(max_length=500)
    agency = models.CharField(max_length=200)
    status = models.CharField(max_length=200, choices=[("awarded", "awarded"), ("pending", "pending")])
    year = models.PositiveSmallIntegerField()
    extra_info = models.CharField(max_length=200, blank=True)
    comment = models.CharField(max_length=200, blank=True)

    # return a string representation of the object
    def __str__(self):
        # return date year and title
        return str(self.year) + " - " + self.title


#    Skills
# ---------------------------------------------------------------------------- #
class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=100)
    skills = models.TextField(verbose_name='Skills (CV and website)')
    skills_short = models.TextField(verbose_name='Skills (resume)')

    def __str__(self):
        return self.name


#    Leadership
# ---------------------------------------------------------------------------- #

class Leadership(models.Model):
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200)
    featured = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title + " at " + self.organization.short_name


#    Honors and Awards
# ---------------------------------------------------------------------------- #

class HonorAndAward(models.Model):
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200, blank=True)
    featured = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title


#    Research advising
# ---------------------------------------------------------------------------- #

class Advising(models.Model):
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    degree_type = models.CharField(max_length=200, choices=[("Doctoral", "Doctoral"), ("Master's", "Master's"), ("Bachelor's", "Bachelor's"), ("Other", "Other")])
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    positions = models.CharField(max_length=200)
    diversity_tags = models.ManyToManyField(DiversityTag, blank=True)
    organizations = models.CharField(max_length=200)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    def __str__(self):
        return self.name

    def journey(self):
        journey = []
        for item in zip(self.positions.split(", "), self.organizations.split(", ")):
            string = item[0] + (" (" + item[1] + ")" if item[1] != '*' else '')
            journey.append(string)
        return ' > '.join(journey)

    def journey_short(self):
        journey = []
        for item in zip(self.positions.split(", "), self.organizations.split(", ")):
            string = item[0] + (" (" + item[1] + ")" if item[1] != '*' else '')
            journey.append(string)
        if len(journey) < 3:
            return ' > '.join(journey)
        else:
            return journey[0] + " >>> " + journey[-1]

    def get_first_name(self):
        if self.name[-1] == '*':
            return self.name.split(' ')[0] + '*'
        else:
            return self.name.split(' ')[0]


#    Mentoring
# ---------------------------------------------------------------------------- #

class Mentoring(models.Model):
    name = models.CharField(max_length=200)
    program = models.CharField(max_length=200, choices=[("MSE Industry Mentoring", "MSE Industry Mentoring"), ("Mentor Jackets", "Mentor Jackets"), ("IITR AMP", "IITR AMP"), ("Other", "Other")])
    degree_type = models.CharField(max_length=200, choices=[("Doctoral", "Doctoral"), ("Master's", "Master's"), ("Bachelor's", "Bachelor's"), ("Other", "Other")])
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    positions = models.CharField(max_length=200)
    diversity_tags = models.ManyToManyField(DiversityTag, blank=True)
    organizations = models.CharField(max_length=200)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    def __str__(self):
        return self.name
    def journey(self):
        journey = []
        for item in zip(self.positions.split(", "), self.organizations.split(", ")):
            string = item[0] + (" (" + item[1] + ")" if item[1] != '*' else '')
            journey.append(string)
        return ' > '.join(journey)
    def journey_short(self):
        journey = []
        for item in zip(self.positions.split(", "), self.organizations.split(", ")):
            string = item[0] + (" (" + item[1] + ")" if item[1] != '*' else '')
            journey.append(string)
        if len(journey) < 3:
            return ' > '.join(journey)
        else:
            return journey[0] + " >>> " + journey[-1]
    def get_first_name(self):
        return self.name.split(' ')[0]


#    Teaching
# ---------------------------------------------------------------------------- #

class Teaching(models.Model):
    
        # define the fields
        course_name = models.CharField(max_length=200, blank=True)
        topic = models.CharField(max_length=200, blank=True)
        course_code = models.CharField(max_length=100)
        topic = models.CharField(max_length=200, blank=True)
        # use the organization name field from the Organizations model
        organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
        position = models.CharField(max_length=200)
        year = models.PositiveSmallIntegerField()
        semester = models.CharField(max_length=200, choices=[("Fall", "Fall"), ("Spring", "Spring"), ("Summer", "Summer")], blank=True)
    
        # return a string representation of the object
        def __str__(self):
            return self.course_code


#    Work highlights (not used any more)
# ---------------------------------------------------------------------------- #

class WorkHighlight(models.Model):

    # define the fields
    title = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
    position = models.CharField(max_length=200, blank=True)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField(blank=True, null=True)
    description = models.TextField()
    image = models.ImageField(upload_to='images/work_highlights', blank=True)

    # return a string representation of the object
    def __str__(self):
        return self.title


#    References
# ---------------------------------------------------------------------------- #

class Reference(models.Model):

    # define the fields
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    position = models.CharField(max_length=200)
    email = models.EmailField()
    start_year = models.PositiveSmallIntegerField()
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    is_favorite = models.BooleanField(default=False)

    # return a string representation of the object
    def __str__(self):
        return self.name


#    Scientific reviews
# ---------------------------------------------------------------------------- #

class Review(models.Model):
    
        # define the fields
        venue = models.ForeignKey(Venue, related_name='reviews', on_delete=models.CASCADE)
        featured = models.BooleanField(default=False)
        articles_reviewed = models.PositiveIntegerField(default=1)
    
        # return a string representation of the object
        def __str__(self):
            return self.venue.name


#    ANALYTICS
# ---------------------------------------------------------------------------- #

class Analytic(models.Model):
    visited_page = models.CharField(max_length=50, default='/')
    remote_addr = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.CharField(max_length=100, null=True)
    http_accept_language = models.CharField(max_length=50, null=True)
    http_host = models.CharField(max_length=50, null=True)
    http_referer = models.CharField(max_length=100, null=True)
    http_user_agent = models.CharField(max_length=400, null=True)
    remote_host = models.CharField(max_length=50, null=True)
    remote_user = models.CharField(max_length=50, null=True)
    remote_port = models.CharField(max_length=50, null=True)
    request_method = models.CharField(max_length=50, null=True)
    server_name = models.CharField(max_length=50, null=True)
    server_port = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.remote_addr + " " + self.timestamp.strftime("%Y-%m-%d")
