from django.contrib import admin
# import the model objects from the model file
from .models import Organization, DiversityTag, PublicationTag, PublicationType, BasicInformation, Education, Experience, GoogleScholar, Venue, VenueMetric, Publication, Presentation, Proposal, SkillCategory, Leadership, HonorAndAward, Advising, Mentoring, Teaching, WorkHighlight, Message, Reference, Review, Analytic


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
            'fields': ('website_tagline', 'cv_tagline', 'resume_tagline', 'website_statement', 'personal_statement', 'resume_statement', 'cv_statement', 'extra_curricular')
            }),
        ('Websites', {
            'fields': ('website_url', 'scholar_url', 'researchgate_url', 'orcid_url', 'publons_url', 'facebook_url', 'twitter_url', 'linkedin_url', 'github_url', 'instagram_url', 'snapchat_url', 'youtube_url', 'medium_url', 'towardsdatascience_url')
            }),
    )

class MessageAdmin(admin.ModelAdmin):
    list_display = ('senders_name', 'senders_email', 'message', 'timestamp', 'hidden_field')
    list_filter = ['timestamp', 'senders_name']
    search_fields = ['senders_name', 'senders_email', 'message']
    def save_model(self, request, obj, form, change):
        obj.save(using='messages')

class PublicationsAdmin(admin.ModelAdmin):
    list_display = ('date', 'featured', 'title', 'status', 'doi', 'venue')
    list_editable = ('featured',)
    ordering = ('-date', '-pk')
    search_fields = ['title', 'authors', 'publisher', 'doi']
    fieldsets = (
        (None, {'fields': ('title', 'authors', 'venue', 'publisher', 'volume', 'issue', 'pages', 'article_number', 'publication_types', 'keywords', 'date', 'doi', 'abstract', 'information_confirmed', 'citations', 'citations_updated_on', 'link')}),
        ('Website', {'fields': ('featured', 'status', 'published_version', 'comment', 'tags')}),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'published_version':
            kwargs['queryset'] = Publication.objects.order_by('title')
        elif db_field.name == 'venue':
            kwargs['queryset'] = Venue.objects.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class VenueMetricInline(admin.TabularInline):
    model = VenueMetric
    extra = 0


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0


class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'publisher', 'kind', 'issn', 'eissn')
    search_fields = ('name', 'publisher', 'issn', 'eissn', 'acronym')
    inlines = (VenueMetricInline, ReviewInline)


class VenueMetricAdmin(admin.ModelAdmin):
    list_display = ('venue', 'metric_type', 'year', 'value', 'verified_on')
    list_filter = ('metric_type', 'year')
    search_fields = ('venue__name',)

class PresentationAdmin(admin.ModelAdmin):
    list_display = ('date', 'featured', 'title', 'conference', 'city', 'comment')
    list_editable = ('featured',)
    ordering = ('-date', '-pk')
    search_fields = ['title', 'authors', 'city', 'doi']
    fieldsets = (
        (None, {'fields': ('title', 'authors', 'conference', 'container_title', 'volume', 'issue', 'pages', 'article_number', 'publication_type', 'date', 'doi', 'abstract', 'citations', 'link')}),
        ('Presentation', {'fields': ('speaker_index', 'city', 'state', 'country')}),
        ('Website', {'fields': ('featured', 'information_confirmed', 'comment', 'tags')}),
    )

class ProposalAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'status', 'pi')
    search_fields = ['title', 'pi', 'agency']

class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('id',)
    fields = ('name', 'skills', 'skills_short')

class LeadershipAdmin(admin.ModelAdmin):
    list_display = ('title', 'featured', 'organization', 'start_date')
    list_editable = ('featured',)

class HonorAndAwardAdmin(admin.ModelAdmin):
    list_display = ('title', 'featured', 'organization', 'start_date')
    list_editable = ('featured',)

class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'organization', 'start_year', 'is_favorite')
    list_filter = ('is_favorite',)
    list_editable = ('is_favorite',)

class TeachingAdmin(admin.ModelAdmin):
    list_display = ('year', 'semester', 'course_code', 'topic')
    save_as = True

class WorkHighlightAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'start_year')

class AnalyticAdmin(admin.ModelAdmin):
    list_display = ('remote_addr', 'visited_page', 'http_host', 'http_referer', 'timestamp')
    # sort by timestamp
    ordering = ('-timestamp',)
    search_fields = ['http_user_agent', 'visited_page']
    def save_model(self, request, obj, form, change):
        obj.save(using='analytics')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('venue', 'featured', 'articles_reviewed')
    list_editable = ('featured', 'articles_reviewed')
    list_editable = ('articles_reviewed',)
    search_fields = ('venue__name',)
    # sort by timestamp
    ordering = ('venue__name',)

class GoogleScholarAdmin(admin.ModelAdmin):
    list_display = ('citations', 'h_index', 'i10_index', 'updated_at')
    readonly_fields = ('citations', 'h_index', 'i10_index', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# registrations should be on separate lines for each object or passed as a list
admin.site.register(Organization)
admin.site.register(DiversityTag)
admin.site.register(PublicationTag)
admin.site.register(PublicationType)
admin.site.register(BasicInformation, BasicInformationAdmin)
admin.site.register(GoogleScholar, GoogleScholarAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(VenueMetric, VenueMetricAdmin)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(Message, MessageAdmin)
admin.site.register(Publication, PublicationsAdmin)
admin.site.register(Presentation, PresentationAdmin)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(SkillCategory, SkillCategoryAdmin)
admin.site.register(Leadership, LeadershipAdmin)
admin.site.register(HonorAndAward, HonorAndAwardAdmin)
admin.site.register(Advising)
admin.site.register(Mentoring)
admin.site.register(Teaching, TeachingAdmin)
admin.site.register(WorkHighlight, WorkHighlightAdmin)
admin.site.register(Reference, ReferenceAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Analytic, AnalyticAdmin)