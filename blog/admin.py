from django.contrib import admin
from .models import Category, Tag, Reference, Post

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'hidden')
    ordering = ('name',) # should be a tuple/list, throws error without a , 

class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    ordering = ('name',) # should be a tuple/list, throws error without a ,

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'featured', 'publication_date')
    search_fields = ['title', 'body', 'categories', 'tags', 'author']
    ordering = ['-publication_date']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag)
admin.site.register(Reference, ReferenceAdmin)
admin.site.register(Post, PostAdmin)