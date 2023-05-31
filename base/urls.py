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
    path('resume/', views.resume, name='resume'),
    path('resume-fancy/', views.resume_fancy, name='resume-fancy'),
]