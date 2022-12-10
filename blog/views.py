from datetime import datetime
from django.shortcuts import render
from .models import Category, Post, Tag
from base.models import BasicInformation, Analytic

import library.core_website_functions as core


#    Common straightforward database imports
# ---------------------------------------------------------------------------- #

category_list = Category.objects.filter(hidden=False).order_by('display_order')
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


#    BLOG: Category page
# ---------------------------------------------------------------------------- #

def category(request, category_id):
    
        # Add user visit to database
        # -------------------------------------------#
        core.add_user_info_to_database(Analytic(), request, '/blog/category/' + str(category_id))
    
        # Gather information from the database here
        if category_id:
            category = Category.objects.get(pk=category_id)
            category_posts = published_posts.filter(categories=category).order_by('-publication_date') if category else None
    
        context = {
            'basic_info': basic_info,
            'first_name': basic_info.first_name,
            'last_name': basic_info.last_name,
            'category_list': category_list,
            'recent_posts': recent_posts,
            'category': category if category else None,
            'category_posts': category_posts,
        }
    
        return render(request, 'blog/category.html', context)


#    BLOG: Tag page
# ---------------------------------------------------------------------------- #

def tag(request, tag_id):
    
        # Add user visit to database
        # -------------------------------------------#
        core.add_user_info_to_database(Analytic(), request, '/blog/tag/' + str(tag_id))
    
        # Gather information from the database here
        if tag_id:
            tag = Tag.objects.get(pk=tag_id)
            tag_posts = published_posts.filter(tags=tag).order_by('-publication_date') if tag else None
        
        context = {
            'basic_info': basic_info,
            'first_name': basic_info.first_name,
            'last_name': basic_info.last_name,
            'category_list': category_list,
            'recent_posts': recent_posts,
            'tag': tag if tag else None,
            'tag_posts': tag_posts,
        }
    
        return render(request, 'blog/tag.html', context)