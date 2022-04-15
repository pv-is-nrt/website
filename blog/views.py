from datetime import datetime
from django.shortcuts import render
from .models import Category, Post
from base.models import BasicInformation, Analytic

import core.core_website_functions as core


#    Common straightforward database imports
# ---------------------------------------------------------------------------- #

category_list = Category.objects.filter(hidden=False)
# select posts with publication date in the past
# TODO: check how to properly get only published posts
published_posts = Post.objects.filter(publication_date__lte=datetime.now()).order_by('-publication_date')
recent_posts = published_posts[:10]

# imports from other apps
basic_info = BasicInformation.objects.get(pk=1)


#    BLOG: Index page
# ---------------------------------------------------------------------------- #

def index(request):

    # Add user visit to database
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/blog')

    # Gather information from the database here
    context = {
        'basic_info': basic_info,
        'first_name': basic_info.first_name,
        'last_name': basic_info.last_name,
        'category_list': category_list,
        'recent_posts': recent_posts,
    }

    return render(request, 'blog/index.html', context)


#    BLOG: Post page
# ---------------------------------------------------------------------------- #

def post(request, post_id):

    # Add user visit to database
    # -------------------------------------------#
    core.add_user_info_to_database(Analytic(), request, '/blog/post/' + str(post_id))

    # Gather information from the database here
    if post_id:
        post = Post.objects.get(pk=post_id)
    
    context = {
        'basic_info': basic_info,
        'first_name': basic_info.first_name,
        'last_name': basic_info.last_name,
        'category_list': category_list,
        'recent_posts': recent_posts,
        'post': post if post else None,
    }

    return render(request, 'blog/post.html', context)