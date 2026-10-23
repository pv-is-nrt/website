# django related imports
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import date, timedelta
import json
from .models import BasicInformation, Education, Experience, GoogleScholar, Venue, VenueMetric, Publication, PublicationType, Presentation, Proposal, SkillCategory, Leadership, HonorAndAward, Advising, Mentoring, Teaching, Message, WorkHighlight, Reference, Review, Analytic
# import models from other apps
from blog.models import Post
# Email
from django.core.mail import send_mail

# non-django imports
import library.core_website_functions as core
import math
from .crossref import fetch_many
from .scholar_citations import (
    ScholarCitationLookupError,
    lookup_profile_data,
    normalize_title,
    scholar_user_id,
)

#    Helper function to get common context (fetches fresh data per request)
# ---------------------------------------------------------------------------- #

def _get_common_context():
    """Fetch all common database context fresh on each request to avoid caching issues."""
    # Common straightforward database imports
    basic_info = BasicInformation.objects.get(pk=1)
    educations = Education.objects.order_by('-start_date') # reverse order
    experiences = Experience.objects.order_by('-start_date') # reverse order
    publications = Publication.objects.select_related('venue').order_by('-status', '-date') # reverse order
    presentations = Presentation.objects.order_by('-date') # reverse order
    proposals = Proposal.objects.order_by('-year') # reverse order
    skills_categories = SkillCategory.objects.order_by('id')
    leaderships = Leadership.objects.order_by('-start_date') # reverse order
    honor_and_awards = HonorAndAward.objects.order_by('-start_date') # reverse order
    advisings = Advising.objects.order_by('-start_date') # reverse order
    mentorings = Mentoring.objects.order_by('-start_date') # reverse order
    teachings = Teaching.objects.order_by('-year') # reverse order, TODO add semester ordering
    work_highlights = WorkHighlight.objects.order_by('-start_year')
    references = Reference.objects.filter(is_favorite=True).order_by('start_year')
    reviews = Review.objects.select_related('venue').prefetch_related('venue__metrics').order_by('venue__name')
    
    # imports from other apps
    # import a maximum of six featured posts from the blog app ordered by most recent first
    posts_featured = Post.objects.filter(featured=True).order_by('-publication_date')[:6]
    
    # Common but calculated things
    publications_published = Publication.objects.filter(status='published').order_by('-date')
    publications_featured = Publication.objects.select_related('venue').prefetch_related('venue__metrics').filter(featured=True).order_by('-date')
    # query database to find publications where author starts with Verma
    publications_first_author = Publication.objects.filter(authors__startswith='P Verma')
    publications_published_or_submitted = Publication.objects.filter(status='published').order_by('-date') | Publication.objects.filter(status='under review / submitted').order_by('-date')
    
    presentations_featured = Presentation.objects.filter(featured=True).order_by('-date')
    honor_and_awards_featured = HonorAndAward.objects.filter(featured=True).order_by('-start_date')
    leaderships_featured = Leadership.objects.filter(featured=True).order_by('-start_date')
    reviews_featured = Review.objects.filter(featured=True).select_related('venue').order_by('venue__name')
    # calculate the number of advisings where the name field ends in a certain string
    count_direct_advising = len(Advising.objects.filter(name__endswith='*'))
    # get the distinct program values from the mentorings table
    mentorings_programs = Mentoring.objects.values_list('program', flat=True).distinct()
    # add the length of advisings and mentorings
    total_advisings_mentorings = len(advisings) + len(mentorings)
    
    # Diversity index calculation
    # get the distinct program values from the mentorings table and count them
    mentorings_programs_count = len(mentorings_programs)
    # get the count of advisings
    advisings_count = len(advisings)
    # calculate the diversity index
    diversity_index = math.ceil(math.sqrt(mentorings_programs_count * advisings_count))
    
    return {
        # Basic info
        'basic_info': basic_info,
        # Education and experiences
        'educations': educations,
        'experiences': experiences,
        # Publications
        'publications': publications,
        'publications_published': publications_published,
        'publications_featured': publications_featured,
        'publications_first_author': publications_first_author,
        'publications_published_or_submitted': publications_published_or_submitted,
        # Presentations
        'presentations': presentations,
        'presentations_featured': presentations_featured,
        # Proposals
        'proposals': proposals,
        # Skills
        'skills_categories': skills_categories,
        # Leadership
        'leaderships': leaderships,
        'leaderships_featured': leaderships_featured,
        # Honors and awards
        'honor_and_awards': honor_and_awards,
        'honor_and_awards_featured': honor_and_awards_featured,
        # Advising and mentoring
        'advisings': advisings,
        'count_direct_advising': count_direct_advising,
        'mentorings': mentorings,
        'mentorings_programs': mentorings_programs,
        'total_advisings_mentorings': total_advisings_mentorings,
        # Teaching
        'teachings': teachings,
        # Diversity index
        'diversity_index': diversity_index,
        # Work highlights
        'work_highlights': work_highlights,
        # References
        'references': references,
        # Reviews
        'reviews': reviews,
        'reviews_featured': reviews_featured,
        # Blog posts
        'posts_featured': posts_featured,
    }


def _get_cv_publications():
    publications = list(Publication.objects.select_related('venue').prefetch_related('venue__metrics').exclude(
        publication_types__name='preprint'
    ).order_by('-status', '-date'))
    preprints = Publication.objects.select_related('venue').prefetch_related('venue__metrics').filter(
        publication_types__name='preprint',
        published_version__isnull=True,
    ).order_by('-date')
    publication_sections = []
    for publication in publications:
        if not publication_sections or publication_sections[-1]['grouper'] != publication.status:
            publication_sections.append({'grouper': publication.status, 'list': []})
        publication_sections[-1]['list'].append(publication)

    if preprints:
        under_review_index = next(
            (index for index, section in enumerate(publication_sections)
             if section['grouper'] == 'under review / submitted'),
            None,
        )
        if under_review_index is not None:
            insert_index = under_review_index + 1
        else:
            insert_index = next(
                (index for index, section in enumerate(publication_sections)
                 if section['grouper'] == 'published'),
                len(publication_sections),
            )
        publication_sections.insert(insert_index, {'is_preprints': True})

    return publications, preprints, publication_sections


def _group_cv_teachings(teachings):
    semester_order = {'Spring': 1, 'Summer': 2, 'Fall': 3}
    grouped_teachings = {}
    for teaching in teachings:
        key = (
            teaching.organization_id,
            teaching.position,
            teaching.course_code,
            teaching.topic,
            teaching.course_name,
        )
        if key not in grouped_teachings:
            grouped_teachings[key] = {'teaching': teaching, 'offerings': set()}
        grouped_teachings[key]['offerings'].add((
            teaching.year,
            semester_order.get(teaching.semester, 0),
            teaching.semester,
        ))

    grouped = []
    for item in grouped_teachings.values():
        teaching = item['teaching']
        offerings = sorted(item['offerings'], reverse=True)
        teaching.cv_offering_labels = [
            str(year) for year in sorted({year for year, _, _ in offerings})
        ]
        teaching.cv_latest_year = offerings[0][0]
        teaching.cv_latest_semester_order = offerings[0][1]
        grouped.append(teaching)
    return grouped


def _get_cv_teachings():
    teachings = list(Teaching.objects.select_related('organization'))
    semester_order = {'Spring': 1, 'Summer': 2, 'Fall': 3}
    latest_by_organization = {}
    for teaching in teachings:
        teaching_date = (teaching.year, semester_order.get(teaching.semester, 0))
        latest_by_organization[teaching.organization_id] = max(
            latest_by_organization.get(teaching.organization_id, teaching_date),
            teaching_date,
        )

    teachings = _group_cv_teachings(teachings)
    teachings.sort(key=lambda teaching: (
        -latest_by_organization[teaching.organization_id][0],
        -latest_by_organization[teaching.organization_id][1],
        teaching.organization.full_name.casefold(),
        teaching.position.casefold(),
        -teaching.cv_latest_year,
        -teaching.cv_latest_semester_order,
        teaching.pk,
    ))
    return teachings


def _get_cv_review_groups(reviews):
    grouped_reviews = {}
    for review in reviews:
        venue = review.venue
        impact_factor = next(
            (metric for metric in venue.latest_metrics if metric.metric_type == 'impact_factor'),
            None,
        )
        publisher = venue.publisher.strip()
        if publisher.casefold() in venue.name.casefold():
            publisher = ''
        grouped_reviews.setdefault(venue.kind, []).append({
            'venue': venue,
            'publisher': publisher,
            'impact_factor': impact_factor,
        })

    groups = []
    for kind, label in Venue.KIND_CHOICES:
        kind_reviews = grouped_reviews.get(kind, [])
        kind_reviews.sort(key=lambda item: (
            item['impact_factor'] is None,
            -item['impact_factor'].value if item['impact_factor'] else 0,
            item['venue'].name.casefold(),
        ))
        if kind_reviews:
            groups.append({'label': label, 'reviews': kind_reviews})
    return groups

#    Index page
# -------------------------------------------------------------------- #

@staff_member_required(login_url='/admin/models/login/')
def admin_dashboard(request):
    citation_records = list(Publication.objects.order_by('date', 'pk').values('id', 'title', 'citations', 'citations_updated_on'))
    google_scholar = GoogleScholar.objects.filter(pk=1).first()
    return render(request, 'base/admin_dashboard.html', {
        'citation_records': citation_records,
        'google_scholar': google_scholar,
    })


GOOGLE_SCHOLAR_REFRESH_INTERVAL = timedelta(hours=24)


def _database_citation_total():
    counts_by_title = {}
    publications = Publication.objects.exclude(
        publication_types__name='preprint',
        published_version__isnull=False,
    )
    for title, value in publications.values_list('title', 'citations'):
        try:
            count = int((value or '').replace(',', '').strip())
        except ValueError:
            continue
        title_key = normalize_title(title)
        if title_key:
            counts_by_title[title_key] = max(counts_by_title.get(title_key, 0), count)
    return sum(counts_by_title.values())


def _match_scholar_publications(publications, profile_counts):
    available_counts = profile_counts.copy()
    ordered_publications = sorted(
        publications,
        key=lambda publication: (publication.is_preprint(), publication.pk),
    )
    matched_counts = {}
    matched_titles = set()
    for publication in ordered_publications:
        title_key = normalize_title(publication.title)
        if title_key in available_counts:
            matched_counts[publication.pk] = available_counts.pop(title_key)
            matched_titles.add(title_key)
    return matched_counts, matched_titles


@staff_member_required(login_url='/admin/models/login/')
@require_POST
def admin_update_scholar_citations(request):
    publications = list(Publication.objects.order_by('date', 'pk'))
    today = timezone.localdate()
    now = timezone.now()
    google_scholar, _ = GoogleScholar.objects.get_or_create(pk=1)
    is_fresh = (
        google_scholar.updated_at is not None
        and now - google_scholar.updated_at < GOOGLE_SCHOLAR_REFRESH_INTERVAL
    )
    results = []
    refreshed = False
    fetch_error = None

    if is_fresh:
        for publication in publications:
            results.append({
                'id': publication.pk,
                'title': publication.title,
                'old_count': publication.citations,
                'new_count': publication.citations,
                'updated_on': publication.citations_updated_on.isoformat() if publication.citations_updated_on else '',
                'status': 'Skipped (profile data is less than 24 hours old)',
            })
        message = 'Google Scholar data is current; no request was made.'
    else:
        try:
            profile_url = BasicInformation.objects.get(pk=1).scholar_url
            profile_data = lookup_profile_data(scholar_user_id(profile_url))
        except (BasicInformation.DoesNotExist, ScholarCitationLookupError) as error:
            fetch_error = str(error)
        if fetch_error:
            for publication in publications:
                results.append({
                    'id': publication.pk,
                    'title': publication.title,
                    'old_count': publication.citations,
                    'new_count': publication.citations,
                    'updated_on': publication.citations_updated_on.isoformat() if publication.citations_updated_on else '',
                    'status': fetch_error,
                })
            message = fetch_error
        else:
            google_scholar.citations = profile_data['citations']
            google_scholar.h_index = profile_data['h_index']
            google_scholar.i10_index = profile_data['i10_index']
            google_scholar.updated_at = now

            publications_to_update = []
            profile_counts = profile_data['publication_counts']
            matched_profile_counts, matched_title_keys = _match_scholar_publications(
                publications,
                profile_counts,
            )
            for publication in publications:
                old_count = publication.citations
                key = normalize_title(publication.title)
                citation_count = matched_profile_counts.get(publication.pk)
                if citation_count is None:
                    status = (
                        'Duplicate title (Scholar item matched to another record)'
                        if key in matched_title_keys
                        else 'Not found in Scholar profile'
                    )
                    new_count = old_count
                    updated_on = publication.citations_updated_on.isoformat() if publication.citations_updated_on else ''
                else:
                    publication.citations = str(citation_count)
                    publication.citations_updated_on = today
                    publication.updated_at = now
                    publications_to_update.append(publication)
                    status = 'Updated'
                    new_count = citation_count
                    updated_on = today.isoformat()
                results.append({
                    'id': publication.pk,
                    'title': publication.title,
                    'old_count': old_count,
                    'new_count': new_count,
                    'updated_on': updated_on,
                    'status': status,
                })
            with transaction.atomic():
                google_scholar.save(update_fields=('citations', 'h_index', 'i10_index', 'updated_at'))
                if publications_to_update:
                    Publication.objects.bulk_update(
                        publications_to_update,
                        ('citations', 'citations_updated_on', 'updated_at'),
                    )
            refreshed = True
            message = 'Updated Scholar metrics and matched {} publication(s).'.format(len(publications_to_update))

    return JsonResponse({
        'results': results,
        'google_scholar': {
            'citations': google_scholar.citations,
            'h_index': google_scholar.h_index,
            'i10_index': google_scholar.i10_index,
            'updated_at': google_scholar.updated_at.isoformat() if google_scholar.updated_at else None,
        },
        'refreshed': refreshed,
        'scholar_total': google_scholar.citations,
        'database_total': _database_citation_total(),
        'message': message,
    })


@staff_member_required(login_url='/admin/models/login/')
def admin_crossref(request):
    publications = Publication.objects.select_related('venue').exclude(doi='').order_by('-date')
    records = [
        {'key': 'publication-{}'.format(record.pk), 'type': 'publication', 'id': record.pk, 'doi': record.doi, 'record': record}
        for record in publications
    ]
    records.sort(key=lambda item: item['record'].information_confirmed)
    for item in records:
        record = item['record']
        abstract_words = len(record.abstract.split())
        item['status_tags'] = []
        item['listing_alert'] = not record.information_confirmed
        if not record.information_confirmed:
            item['status_tags'].append({'label': 'Information not confirmed', 'kind': 'alert'})
        if not record.abstract:
            item['status_tags'].append({'label': 'Abstract missing', 'kind': 'alert'})
        elif abstract_words < 50:
            item['status_tags'].append({'label': 'Abstract too short', 'kind': 'alert'})
        if not record.date:
            item['status_tags'].append({'label': 'Date missing', 'kind': 'alert'})
        item['status_tags'].append({'label': 'Last updated: {}'.format(record.updated_at.strftime('%Y-%m-%d')), 'kind': 'updated'})
    context = {'records': records, 'preview': [], 'message': request.session.pop('crossref_message', None)}

    if request.method == 'POST' and request.POST.get('action') == 'preview':
        selected = [record for record in records if record['key'] == request.POST.get('record_key')]
        mailto = getattr(settings, 'EMAIL_HOST_USER', '')
        context['preview'] = fetch_many(selected, mailto)
        for item in context['preview']:
            item['record'] = next(record['record'] for record in records if record['key'] == item['record_key'])
            item['fields'] = []
            if item['ok']:
                field_names = ('doi', 'title', 'authors', 'container_title', 'publisher', 'venue_publisher', 'volume', 'issue', 'pages', 'article_number', 'publication_type', 'keywords', 'date', 'abstract', 'link', 'citations')
                for field in field_names:
                    crossref_field = 'publisher' if field == 'venue_publisher' else field
                    current_value = getattr(item['record'], field, '')
                    if field == 'container_title':
                        current_value = item['record'].venue.name if item['record'].venue else ''
                    elif field == 'venue_publisher':
                        current_value = item['record'].venue.publisher if item['record'].venue else ''
                    proposed_value = item['metadata'].get(crossref_field, '')
                    if field == 'publication_type':
                        type_names = list(item['record'].publication_types.values_list('name', flat=True))
                        current_value = ', '.join(type_names)
                    item['fields'].append({
                        'name': field,
                        'label': (
                            'Date ({})'.format(item['metadata'].get('date_source'))
                            if field == 'date' and item['metadata'].get('date_source')
                            else field.replace('_', ' ').title()
                        ),
                        'current': current_value.isoformat() if hasattr(current_value, 'isoformat') else current_value,
                        'proposed': proposed_value,
                        'changed': proposed_value not in type_names if field == 'publication_type' else str(current_value) != str(proposed_value),
                        'apply_by_default': (
                            field == 'venue_publisher'
                            and not current_value
                            and bool(proposed_value)
                        ) or (
                            field == 'abstract'
                            and bool(proposed_value)
                            and len(str(proposed_value).split()) >= len(str(current_value).split())
                        ) or (
                            field == 'date'
                            and not current_value
                            and bool(proposed_value)
                        ) or (
                            field not in ('abstract', 'date', 'venue_publisher')
                            and str(current_value) != str(proposed_value)
                            and bool(proposed_value)
                        ),
                        'editable': field in ('title', 'abstract'),
                        'input_name': 'apply_{}_{}'.format(item['record_key'], field),
                        'value_input_name': 'value_{}_{}'.format(item['record_key'], field),
                    })
                item['fields'].append({
                    'name': 'information_confirmed',
                    'label': 'Information confirmed',
                    'current': 'Yes' if item['record'].information_confirmed else 'No',
                    'proposed': 'Manual setting',
                    'changed': False,
                    'manual': True,
                    'input_name': 'information_action_{}'.format(item['record_key']),
                })
        request.session['crossref_preview'] = [
            {'record_key': item['record_key'], 'record_type': item['record_type'], 'record_id': item['record_id'], 'metadata': item['metadata']}
            for item in context['preview'] if item['ok']
        ]

    elif request.method == 'POST' and request.POST.get('action') == 'discard':
        request.session.pop('crossref_preview', None)
        return redirect('admin-crossref')

    elif request.method == 'POST' and request.POST.get('action') == 'apply':
        preview = request.session.pop('crossref_preview', [])
        applied = 0
        for item in preview:
            record = Publication.objects.filter(pk=item['record_id']).first()
            if not record:
                continue
            fields = ('doi', 'title', 'authors', 'container_title', 'publisher', 'venue_publisher', 'volume', 'issue', 'pages', 'article_number', 'publication_type', 'keywords', 'date', 'abstract', 'link', 'citations')
            for field in fields:
                if 'apply_{}_{}'.format(item['record_key'], field) not in request.POST:
                    continue
                value = request.POST.get('value_{}_{}'.format(item['record_key'], field), '')
                if field not in ('title', 'abstract'):
                    metadata_field = 'publisher' if field == 'venue_publisher' else field
                    value = item['metadata'].get(metadata_field, getattr(record, field, ''))
                if field == 'container_title':
                    venue_name = str(value).strip()
                    if venue_name:
                        venue = Venue.objects.filter(name__iexact=venue_name).first()
                        if venue is None:
                            venue = Venue.objects.create(name=venue_name)
                        record.venue = venue
                    else:
                        record.venue = None
                    continue
                if field == 'venue_publisher':
                    if record.venue:
                        record.venue.publisher = value
                        record.venue.save(update_fields=('publisher',))
                    continue
                if field == 'publication_type':
                    if value:
                        publication_type, _ = PublicationType.objects.get_or_create(name=value)
                        record.publication_types.add(publication_type)
                    continue
                if field == 'date' and isinstance(value, str) and len(value) == 10:
                    value = date.fromisoformat(value)
                setattr(record, field, value)
            information_action = request.POST.get('information_action_{}'.format(item['record_key']))
            if information_action == 'confirmed':
                record.information_confirmed = True
            elif information_action == 'unconfirmed':
                record.information_confirmed = False
            record.save()
            applied += 1
        request.session['crossref_message'] = '{} publication{} confirmed against Crossref.'.format(applied, '' if applied == 1 else 's')
        return redirect('admin-crossref')

    return render(request, 'base/admin_crossref.html', context)


#    Index page
# -------------------------------------------------------------------- #

def index(request):

    # ADD USER VISIT INFO TO DATABASE
    # make sure to add to each view that you want to track
    # NOTE: IN EACH APP
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/')

    # Just set debug_info to whatever you want to print on homepage
    debug_info = None

    # create a context here
    context = _get_common_context()
    # Override with homepage-specific values if needed
    context['first_name'] = context['basic_info'].first_name
    context['last_name'] = context['basic_info'].last_name
    context['debug_info'] = debug_info

    # For later use: this is how to raise 404
    # pk = 1 will not raise error, but pk = 2 will because the table has only one row
    # o = get_object_or_404(BasicInformation, pk=2)

    # return the rendered page here
    return render(request, 'base/index.html', context)


#    Professional page
# -------------------------------------------------------------------- #

def professional(request):
    
    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/professional')

    # get the complete file path of CV and resume
    cv_path = settings.BASE_DIR / 'base/static/base/docs/Prateek Verma - CV.pdf'
    resume_path = settings.BASE_DIR / 'base/static/base/docs/Prateek Verma - Resume.pdf'

    # get the modified date of the CV and resume files
    cv_mod = core.get_last_modified_date(cv_path)
    resume_mod = core.get_last_modified_date(resume_path)

    # Gather information from the database here

    # create a context here
    context = _get_common_context()
    # Add professional page specific values
    context['first_name'] = context['basic_info'].first_name
    context['last_name'] = context['basic_info'].last_name
    context['cv_mod'] = cv_mod
    context['resume_mod'] = resume_mod

    # return the rendered page here
    return render(request, 'base/professional.html', context)


def publications(request):
    context = _get_common_context()
    context['publications'] = Publication.objects.select_related('venue').order_by('-date', 'title')
    context['presentations'] = Presentation.objects.order_by('-date', 'title')
    context['first_name'] = context['basic_info'].first_name
    context['last_name'] = context['basic_info'].last_name
    return render(request, 'base/publications.html', context)


#    Contact page
# -------------------------------------------------------------------- #

def contact(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/contact')

    # to hold the contact form message
    messages_object = Message()

    # create a context here
    context = _get_common_context()
    # Add contact page specific values
    context['first_name'] = context['basic_info'].first_name
    context['last_name'] = context['basic_info'].last_name

    # process incoming data
    if request.method == 'POST':

        # create constants for posting message to email and forms
        HIDDEN_FIELD = request.POST['country'] # anti-spam hidden field
        SENDERS_NAME = request.POST['senders_name']
        SENDERS_EMAIL = request.POST['senders_email']

        SENDERS_MESSAGE = request.POST['message']

        # TEMP FIXES
        # -------------------------------------------#
        # do nothing, don't save to database nor send an email if the SENDERS_EMAIL ends in .ru
        if SENDERS_EMAIL.endswith('.ru'):
            # create a message to display to the user
            contact_status_message = "Suspicious activity detected. Please try again later, or try differently."
            # add this message to the context
            context['contact_status_message'] = contact_status_message
            return render(request, 'base/contact.html', context)
        # if sender only uses first name only, don't save to database nor send an email
        if len(SENDERS_NAME.split()) == 1:
            # create a message to display to the user
            contact_status_message = "Please enter your full name in the format 'FirstName LastName'."
            # add this message to the context
            context['contact_status_message'] = contact_status_message
            return render(request, 'base/contact.html', context)
        

        MY_NAME = context['basic_info'].first_name + ' ' + context['basic_info'].last_name
        MY_EMAIL = context['basic_info'].contact_email

        # add posted data to the database, whether spam or not
        messages_object.hidden_field = HIDDEN_FIELD
        messages_object.senders_name = SENDERS_NAME
        messages_object.senders_email = SENDERS_EMAIL
        messages_object.message = SENDERS_MESSAGE
        messages_object.save(using='messages')

        # has a spam been detected?
        SPAM_DETECTED = True
        if HIDDEN_FIELD == '' or HIDDEN_FIELD == None:
            SPAM_DETECTED = False

        # construct email related constants >>>

        # subject and message for email that will be sent to me, when someone sends me a message
        SUBJECT_IN = 'Message from ' + SENDERS_NAME + ' (via prateekverma.com)'
        MESSAGE_IN = 'You received a message from\n' + 'Name: ' + SENDERS_NAME + '\n' + 'Email: ' + SENDERS_EMAIL + '\n' + 'Message: ' + SENDERS_MESSAGE

        # subject and message for email that will be sent to user, as a confirmation that I have received their message
        SUBJECT_OUT = 'Message sent to ' + MY_NAME
        MESSAGE_OUT = 'Hi, ' + SENDERS_NAME + '!\n\n' + 'Thank you for contacting me. I have received your message and will get back to you as soon as possible!\n\nSincerely,\n' + MY_NAME + '\n\n' + '--------------------------------------------------------\nThe message you sent was:\n' + SENDERS_MESSAGE

        # send email to user only if it's not a spam
        if SPAM_DETECTED == False:
            # send email to me (NOTE that gmail will rewrite sender's email address to my email/server's address to disallow spoofing)
            # Has been set to throw an error on email send failure only if the requester is localhost
            email_in_success = send_mail(SUBJECT_IN, MESSAGE_IN, SENDERS_NAME + ' <' + SENDERS_EMAIL + '>', [MY_NAME + ' <' + MY_EMAIL + '>'], fail_silently=False if request.META['REMOTE_ADDR'] == '127.0.0.1' else True)
            # send email to user
            email_out_success = send_mail(SUBJECT_OUT, MESSAGE_OUT, MY_NAME + ' <' + MY_EMAIL + '>', [SENDERS_NAME + ' <' + SENDERS_EMAIL + '>'], fail_silently=False if request.META['REMOTE_ADDR'] == '127.0.0.1' else True)
        else:
            # if spam was detected, don't send email and set the email success/failure log to None
            email_in_success = None
            email_out_success = None
            # although the return of send_mail is an integer, the field in database allows None. 0 would mean that there was a problem sending the email, which is not true. Hence we set it to None.

        # add the email success/failure log to the database
        messages_object.email_in_success = email_in_success
        messages_object.email_out_success = email_out_success
        # note that this second save does not create a new row or throw an error. It updates the existing row.
        messages_object.save(using='messages')
        
        # create a message to display to the user
        contact_status_message = "Your message was sent successfully!"
        # add this message to the context
        context['contact_status_message'] = contact_status_message

        return render(request, 'base/contact.html', context)

    # return the rendered page here
    return render(request, 'base/contact.html', context)


#    CV page
# ---------------------------------------------------------------------------- #

def cv(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/cv')

    context = _get_common_context()
    context['cv_teachings'] = _get_cv_teachings()
    context['review_groups'] = _get_cv_review_groups(context['reviews'])
    context['google_scholar'] = GoogleScholar.objects.filter(pk=1).first()
    (
        context['publications'],
        context['preprints'],
        context['publication_sections'],
    ) = _get_cv_publications()
    return render(request, 'base/cv.html', context)

def cv_chen(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/cv-chen')

    context = _get_common_context()
    context['cv_teachings'] = _get_cv_teachings()
    context['review_groups'] = _get_cv_review_groups(context['reviews'])
    context['google_scholar'] = GoogleScholar.objects.filter(pk=1).first()
    (
        context['publications'],
        context['preprints'],
        context['publication_sections'],
    ) = _get_cv_publications()
    return render(request, 'base/cv-chen.html', context)


#    Resume page
# ---------------------------------------------------------------------------- #

def resume(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/resume')

    context = _get_common_context()
    context['google_scholar'] = GoogleScholar.objects.filter(pk=1).first()
    return render(request, 'base/resume.html', context)


def resume_old(request):
    core.add_user_info_to_database(Analytic(), request, '/resume-old')
    context = _get_common_context()
    return render(request, 'base/resume-old.html', context)