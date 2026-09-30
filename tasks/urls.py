from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.index, name='index'),
    path('preferences/', views.preferences, name='preferences'),
    path('api/preferences/', views.update_preferences, name='update-preferences'),
    path('api/create/', views.create, name='create'),
    path('api/categories/create/', views.create_category, name='create-category'),
    path('api/categories/<int:category_id>/update/', views.update_category, name='update-category'),
    path('api/categories/<int:category_id>/delete/', views.delete_category, name='delete-category'),
    path('api/<int:task_id>/update/', views.update, name='update'),
]