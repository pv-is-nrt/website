from django.contrib import admin
# import the model objects from the model file
from .models import Organization, DiversityTag, PublicationTag, BasicInformation, Education, Experience, Publication, Presentation, Proposal, Skillset, Leadership, HonorAndAward, Advising, Mentoring, Teaching, WorkHighlight, Message, Reference, Review, Analytic


# ModelAdmin class definitions

class BasicInformationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'notification_email')
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'birth_date')
            }),
        ('Contact Information', {
            'fields': ('notification_email', 'contact_email', 'personal_email', 'work_email', 'country_phone_code', 'phone', 'address', 'city', 'zip_code', 'country')
            }),
        ('Statements', {
            'fields': ('website_tagline', 'resume_tagline', 'website_statement', 'personal_statement', 'extra_curricular')
            }),
        ('Websites', {
            'fields': ('website_url', 'scholar_url', 'researchgate_url', 'orcid_url', 'publons_url', 'facebook_url', 'twitter_url', 'linkedin_url', 'github_url', 'instagram_url', 'snapchat_url', 'youtube_url', 'medium_url', 'towardsdatascience_url')
            }),
    )

class MessageAdmin(admin.ModelAdmin):
    list_display = ('senders_name', 'senders_email', 'message', 'timestamp', 'hidden_field')
    list_filter = ['timestamp', 'senders_name']
    search_fields = ['senders_name', 'senders_email', 'message']

class PublicationsAdmin(admin.ModelAdmin):
    list_display = ('date', 'featured', 'title', 'status', 'publisher')
    search_fields = ['title', 'authors', 'publisher']

class PresentationAdmin(admin.ModelAdmin):
    list_display = ('date', 'featured', 'title', 'city')
    search_fields = ['title', 'presenter', 'city']

class ProposalAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'status', 'pi')
    search_fields = ['title', 'pi', 'agency']

class SkillsetAdmin(admin.ModelAdmin):
    list_display = ('category', 'group', 'order')

class HonorAndAwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'featured', 'organization', 'start_date')

class TeachingAdmin(admin.ModelAdmin):
    list_display = ('year', 'semester', 'course_code', 'topic')

class WorkHighlightAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'start_year')

class AnalyticAdmin(admin.ModelAdmin):
    list_display = ('remote_addr', 'visited_page', 'http_host', 'http_referer', 'timestamp')
    # sort by timestamp
    ordering = ('-timestamp',)
    search_fields = ['http_user_agent', 'page']

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('featured', 'publication')
    search_fields = ['publication']
    # sort by timestamp
    ordering = ('publication',)


# registrations should be on separate lines for each object or passed as a list
admin.site.register(Organization)
admin.site.register(DiversityTag)
admin.site.register(PublicationTag)
admin.site.register(BasicInformation, BasicInformationAdmin)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Message, MessageAdmin)
admin.site.register(Publication, PublicationsAdmin)
admin.site.register(Presentation, PresentationAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(Skillset, SkillsetAdmin)
admin.site.register(Leadership)
admin.site.register(HonorAndAward, HonorAndAwardAdmin)
admin.site.register(Advising)
admin.site.register(Mentoring)
admin.site.register(Teaching, TeachingAdmin)
admin.site.register(WorkHighlight, WorkHighlightAdmin)
admin.site.register(Reference)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Analytic, AnalyticAdmin)