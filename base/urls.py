# django related imports
from django.urls import path
from . import views

# non-django imports


# use name of the current directory as app_name
app_name = 'base'

urlpatterns = [
    path('', views.index, name='index'),
    path('professional/', views.professional, name='professional'),
    path('contact/', views.contact, name='contact'),
    path('cv/', views.cv, name='cv'),
    path('cv-classic/', views.cv_classic, name='cv-classic'),
    path('cv-arial/', views.cv_arial, name='cv-arial'),
    path('resume/', views.resume, name='resume'),
    path('resume-classic/', views.resume_classic, name='resume-classic'),
]