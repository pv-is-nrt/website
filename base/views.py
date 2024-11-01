# django related imports
from django.conf import settings
from django.shortcuts import render
from .models import BasicInformation, Education, Experience, Publication, Presentation, Proposal, Skillset, Skill, SkillCategory, Leadership, HonorAndAward, Advising, Mentoring, Teaching, Message, WorkHighlight, Reference, Review, Analytic
# import models from other apps
from blog.models import Post
# Email
from django.core.mail import send_mail

# non-django imports
import library.core_website_functions as core
import math


#    Common straightforward database imports
# ---------------------------------------------------------------------------- #

basic_info = BasicInformation.objects.get(pk=1)
educations = Education.objects.order_by('-start_date') # reverse order
experiences = Experience.objects.order_by('-start_date') # reverse order
publications = Publication.objects.order_by('-status', '-date') # reverse order
presentations = Presentation.objects.order_by('-date') # reverse order
proposals = Proposal.objects.order_by('-year') # reverse order
skillsets = Skillset.objects.order_by('group', 'order')
# note the ordering by group is important for grouping in the template
skills_categories = SkillCategory.objects.order_by('group', 'order')
# get all skills ordered by score
skills = Skill.objects.order_by('-score')
leaderships = Leadership.objects.order_by('-start_date') # reverse order
honor_and_awards = HonorAndAward.objects.order_by('-start_date') # reverse order
advisings = Advising.objects.order_by('-start_date') # reverse order
mentorings = Mentoring.objects.order_by('degree_type', '-start_date') # reverse order
teachings = Teaching.objects.order_by('-year') # reverse order, TODO add semester ordering
work_highlights = WorkHighlight.objects.order_by('-start_year')
references = Reference.objects.order_by('start_year')
reviews = Review.objects.order_by('publication') # reverse order

# imports from other apps
# import a maximum of six featured posts from the blog app ordered by most recent first
posts_featured = Post.objects.filter(featured=True).order_by('-publication_date')[:6]


#    Common but calculated things
# ---------------------------------------------------------------------------- #

publications_published = Publication.objects.filter(status='published').order_by('-date')
publications_featured = Publication.objects.filter(featured=True).order_by('-date')
# query database to find publications where author starts with Verma
publications_first_author = Publication.objects.filter(authors__startswith='P Verma')
publications_published_or_submitted = Publication.objects.filter(status='published').order_by('-date') | Publication.objects.filter(status='under review / submitted').order_by('-date')

presentations_featured = Presentation.objects.filter(featured=True).order_by('-date')
honor_and_awards_featured = HonorAndAward.objects.filter(featured=True).order_by('-start_date')
leaderships_featured = Leadership.objects.filter(featured=True).order_by('-start_date')
reviews_featured = Review.objects.filter(featured=True).order_by('publication')
# calculate the number of advisings where the name field ends in a certain string
count_direct_advising = len(Advising.objects.filter(name__endswith='*'))
# get the distinct program values from the mentorings table
mentorings_programs = Mentoring.objects.values_list('program', flat=True).distinct()
# add the length of advisings and mentorings
total_advisings_mentorings = len(advisings) + len(mentorings)

#    Diversity index
# ---------------------------------------------------------------------------- #

num_women = len(Advising.objects.filter(diversity_tags__name__contains='women')) + len(Mentoring.objects.filter(diversity_tags__name__contains='women'))

num_african_americans = len(Advising.objects.filter(diversity_tags__name__contains='african americans')) + len(Mentoring.objects.filter(diversity_tags__name__contains='african americans'))

num_internationals = len(Advising.objects.filter(diversity_tags__name__contains='internationals')) + len(Mentoring.objects.filter(diversity_tags__name__contains='internationals'))

num_hispanics = len(Advising.objects.filter(diversity_tags__name__contains='hispanics & latinos')) + len(Mentoring.objects.filter(diversity_tags__name__contains='hispanics & latinos'))

num_first_gen = len(Advising.objects.filter(diversity_tags__name__contains='first-generation college goers')) + len(Mentoring.objects.filter(diversity_tags__name__contains='first-generation college goers'))

num_diversity_total = len(Advising.objects.all()) + len(Mentoring.objects.all())

diversity_women_percent = math.ceil(num_women*100/num_diversity_total)
diversity_african_american_percent = math.ceil(num_african_americans*100/num_diversity_total)
diversity_international_percent = math.ceil(num_internationals*100/num_diversity_total)
diversity_hispanic_percent = math.ceil(num_hispanics*100/num_diversity_total)
diversity_first_gen_percent = math.ceil(num_first_gen*100/num_diversity_total)

# create a diversity index dictionary here
diversity_index = {
                    'women': diversity_women_percent,
                    'hispanics & latinos': diversity_hispanic_percent,
                    'african americans': diversity_african_american_percent,
                    'internationals': diversity_international_percent,
                    'first-gen college goers': diversity_first_gen_percent,
                  }

#    Skills
# ---------------------------------------------------------------------------- #

# find skills with start_year > 2018 and order by start_year
recent_skills = Skill.objects.filter(start_year__gt=2018).order_by('-start_year')


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
    context = {
        # basic information
        'basic_info': basic_info,
        'first_name': basic_info.first_name,
        'last_name': basic_info.last_name,
        'educations': educations,
        'work_highlights': work_highlights,
        'posts_featured': posts_featured,
        'skills_categories': skills_categories,
        'debug_info': debug_info,
    }

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
    context = {
        # basic information
        'basic_info': basic_info,
        'first_name': basic_info.first_name,
        'last_name': basic_info.last_name,
        'experiences': experiences,
        'publications': publications,
        'publications_published': publications_published,
        'publications_first_author': publications_first_author,
        'publications_published_or_submitted': publications_published_or_submitted,
        'presentations': presentations,
        'advisings': advisings,
        'mentorings': mentorings,
        'teachings': teachings,
        'honor_and_awards': honor_and_awards,
        'cv_mod': cv_mod,
        'resume_mod': resume_mod,
    }

    # return the rendered page here
    return render(request, 'base/professional.html', context)


#    Contact page
# -------------------------------------------------------------------- #

def contact(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/contact')

    # to hold the contact form message
    messages_object = Message()

    # create a context here
    context = {
        # basic information
        'basic_info': basic_info,
        'first_name': basic_info.first_name,
        'last_name': basic_info.last_name,
    }

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
        

        MY_NAME = basic_info.first_name + ' ' + basic_info.last_name
        MY_EMAIL = basic_info.contact_email

        # add posted data to the database, whether spam or not
        messages_object.hidden_field = HIDDEN_FIELD
        messages_object.senders_name = SENDERS_NAME
        messages_object.senders_email = SENDERS_EMAIL
        messages_object.message = SENDERS_MESSAGE
        messages_object.save()

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
        messages_object.save()
        
        # create a message to display to the user
        contact_status_message = "Your message was sent successfully!"
        # add this message to the context
        context['contact_status_message'] = contact_status_message

        return render(request, 'base/contact.html', context)

    # return the rendered page here
    return render(request, 'base/contact.html', context)


resume_cv_context = {
        'basic_info': basic_info,
        'educations': educations,
        'experiences': experiences,
        'publications': publications,
        'publications_featured': publications_featured,
        'publications_published': publications_published,
        'publications_first_author': publications_first_author,
        'publications_published_or_submitted': publications_published_or_submitted,
        'presentations': presentations,
        'presentations_featured': presentations_featured,
        'proposals': proposals,
        'skillsets': skillsets,
        'skills_categories': skills_categories,
        'skills': skills,
        'recent_skills': recent_skills,
        'leaderships': leaderships,
        'leaderships_featured': leaderships_featured,
        'honor_and_awards': honor_and_awards,
        'honor_and_awards_featured': honor_and_awards_featured,
        'advisings': advisings,
        'count_direct_advising': count_direct_advising,
        'mentorings': mentorings,
        'mentorings_programs': mentorings_programs,
        'total_advisings_mentorings': total_advisings_mentorings,
        'teachings': teachings,
        'diversity_index': diversity_index,
        'references': references,
        'reviews': reviews,
        'reviews_featured': reviews_featured,
    }


#    CV page
# ---------------------------------------------------------------------------- #

def cv(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/cv')

    context = resume_cv_context
    return render(request, 'base/cv.html', context)


#    Resume page
# ---------------------------------------------------------------------------- #

def resume(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/resume')

    context = resume_cv_context
    return render(request, 'base/resume.html', context)


#    Classic Resume and CV page
# ---------------------------------------------------------------------------- #

def resume_classic(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/resume-classic')

    context = resume_cv_context
    return render(request, 'base/resume-classic.html', context)

def cv_classic(request):

    # ADD USER VISIT INFO TO DATABASE
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/cv-classic')

    context = resume_cv_context
    return render(request, 'base/cv-classic.html', context)