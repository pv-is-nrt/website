from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('post/<int:post_id>', views.post, name='post'),
    path('category/<int:category_id>', views.category, name='category'),
    path('tag/<int:tag_id>', views.tag, name='tag'),
]