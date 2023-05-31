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


#    Basic information
# ---------------------------------------------------------------------------- #

class BasicInformation(models.Model):
    
    # define the fields
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


#    Publications
# ---------------------------------------------------------------------------- #

class Publication(models.Model):

    # define the fields
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500)
    publisher = models.CharField(max_length=200)
    issue_etc = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    doi = models.CharField(max_length=200, blank=True)
    link = models.URLField(blank=True)
    featured = models.BooleanField(default=False)
    citations = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=200, choices=[("under review / submitted", "under review / submitted"), ("submitting next", "submitting next"), ("published", "published"), ("in progress", "in progress"), ("preprint", "preprint")], default="in progress")
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
            if 'P Verma' in self.authors_list()[0:5]:
                return self.authors_list()[0:5] + ["et al."]
            else:
                return self.authors_list()[0:3] + ["...", "P Verma", "et al."]
        else:
            return self.authors_list()
    def authors_list_very_short(self):
        if len(self.authors_list()) > 3:
            if 'P Verma' in self.authors_list()[0:3]:
                return self.authors_list()[0:3] + ["et al."]
            else:
                return self.authors_list()[0:2] + ["...", "P Verma", "et al."]
        else:
            return self.authors_list()


#    Presentations
# ---------------------------------------------------------------------------- #

class Presentation(models.Model):
    # define the fields
    title = models.CharField(max_length=500)
    authors = models.CharField(max_length=500)
    speaker_index = models.PositiveSmallIntegerField()
    conference = models.CharField(max_length=200)
    date = models.DateField()
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=200)
    link = models.URLField(blank=True)
    featured = models.BooleanField(default=False)
    citations = models.CharField(max_length=10, blank=True)
    issue_etc = models.CharField(max_length=200, blank=True)
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
            if 'P Verma' in self.authors_list()[0:3]:
                return self.authors_list()[0:3] + ["et al."]
            else:
                return self.authors_list()[0:2] + ["...", "P Verma", "et al."]
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


#    Skillsets
# ---------------------------------------------------------------------------- #

class Skillset(models.Model):

    # define the fields
    category = models.CharField(max_length=200)
    category_full = models.CharField(max_length=200, blank=True)
    score = models.PositiveSmallIntegerField(blank=True)
    skills = models.TextField()
    order = models.PositiveSmallIntegerField(default=1)
    group = models.CharField(max_length=200, choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")])

    # return a string representation of the object
    def __str__(self):
        return self.category
    # return the skills as a list of skills
    def skills_list_with_score(self):
        skills_list = self.skills.split(", ")
        # sort the skills_list alphabetically
        skills_list.sort(key=str.lower) # so that uppercase does not come before lowercase
        score_list = [item.split('#')[1].strip().strip('*') for item in skills_list]
        skills_list_without_score = [item.split('#')[0].strip() for item in skills_list]
        # zip the lists together
        return list(zip(skills_list_without_score, score_list))
    def skills_list_abbr(self):
        skills_list = self.skills.split(", ")
        # remove the score from the list
        skills_list = [item.split('#')[0].strip().strip('*') for item in skills_list]
        return [item.split(' (')[0] for item in skills_list]
    def skills_list_abbr_with_score(self):
        skills_list = self.skills.split(", ")
        # sort the skills_list alphabetically
        skills_list.sort(key=str.lower) # so that uppercase does not come before lowercase
        score_list = [item.split('#')[1].strip().strip('*') for item in skills_list]
        skills_list_without_score = [item.split('#')[0].strip() for item in skills_list]
        skills_list_abbr = [item.split(' (')[0] for item in skills_list_without_score]
        # zip the lists together
        return list(zip(skills_list_abbr, score_list))


#    Skills
# ---------------------------------------------------------------------------- #

class SkillCategory(models.Model):
    # define the fields
    name = models.CharField(max_length=100)
    score = models.PositiveSmallIntegerField(default=50)
    group = models.CharField(max_length=100, choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")])
    order = models.PositiveSmallIntegerField(default=1)
    hidden = models.BooleanField(default=False)
    # define the methods
    # return a string representation of the object
    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=100, blank=True)
    category = models.ManyToManyField(SkillCategory)
    score = models.PositiveSmallIntegerField(default=50)
    start_year = models.PositiveSmallIntegerField(default=2006) # used to gauge the newness of the skill
    # define the methods
    # return a string representation of the object
    def __str__(self):
        return self.name


#    Leadership
# ---------------------------------------------------------------------------- #

class Leadership(models.Model):

    # define the fields
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200)
    featured = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    # return a string representation of the object
    def __str__(self):
        return self.title + " at " + self.organization.short_name


#    Honors and Awards
# ---------------------------------------------------------------------------- #

class HonorAndAward(models.Model):

    # define the fields
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200, blank=True)
    featured = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    # return a string representation of the object
    def __str__(self):
        return self.title


#    Research advising
# ---------------------------------------------------------------------------- #

class Advising(models.Model):

    # define the fields
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    degree_type = models.CharField(max_length=200, choices=[("Doctoral", "Doctoral"), ("Master's", "Master's"), ("Bachelor's", "Bachelor's"), ("Other", "Other")])
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    # list of positions, starting from under me to present, comma separated
    positions = models.CharField(max_length=200)
    # create a multi-select field for diversity tags
    diversity_tags = models.ManyToManyField(DiversityTag, blank=True)
    # match the positions list
    organizations = models.CharField(max_length=200)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    # return a string representation of the object
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

    # define the fields
    name = models.CharField(max_length=200)
    # add program choices
    program = models.CharField(max_length=200, choices=[("MSE Industry Mentoring", "MSE Industry Mentoring"), ("Mentor Jackets", "Mentor Jackets"), ("IITR AMP", "IITR AMP"), ("Other", "Other")])
    degree_type = models.CharField(max_length=200, choices=[("Doctoral", "Doctoral"), ("Master's", "Master's"), ("Bachelor's", "Bachelor's"), ("Other", "Other")])
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    # list of positions, starting from under me to present, comma separated
    positions = models.CharField(max_length=200)
    # create a multi-select field for diversity tags
    diversity_tags = models.ManyToManyField(DiversityTag, blank=True)
    # match the positions list
    organizations = models.CharField(max_length=200)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)

    # return a string representation of the object
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


#    Work highlights
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

    # return a string representation of the object
    def __str__(self):
        return self.name


#    Scientific reviews
# ---------------------------------------------------------------------------- #

class Review(models.Model):
    
        # define the fields
        publication = models.CharField(max_length=200)
        featured = models.BooleanField(default=False)
    
        # return a string representation of the object
        def __str__(self):
            return self.publication


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
