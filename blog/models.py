from django.db import models
from django.contrib.auth.models import User
from django.utils.deconstruct import deconstructible

# non django imports

#    COMMON CONSTANTS
# ---------------------------------------------------------------------------- #
POST_IMAGE_DIR = 'blog/images/' # BASE MEDIA DIR > APP > IMAGES

#    Cammon classes/functions
# ---------------------------------------------------------------------------- #

# trying to create elaborate filenames is a challenge, somewhat. The upload_to parameter can take a function (with exactly instance and filename as two parameters), but for complicated filenames, more parameters (like the username) might be needed. A function can be wrapped outside the limited (2 instance) function that can take additional parameters. It works fine when tested, but Django migration system is unable to serialize this construction. It won't migrate. A ticket/bug on Django admits this as a limitation of the migration system here (https://code.djangoproject.com/ticket/22999) and advises to use a deconstructible class instead. For example, see this StackOverflow answer: https://stackoverflow.com/a/25768034/2369240.

# NOTE: that we can directly instantiate the class where we need the function to be passed to the upload_to parameter of the FileField.

@deconstructible # needs an import
class uploadPath(object):
    """Used to be a function, but has been modded into a class. Creates a full filepath for a file upload field utilizing a provided root directory and the field's id manually set when defining the field.
    ARGUMENTS FOR INIT:
        root_dir (str): The root directory to use for the file upload. Make sure to include the trailing slash.
        field_id (str): The id of the field to use for the file upload.
    RETURNS:
        (str): The full filepath for the file upload.
    """
    def __init__(self, root_dir, field_id):
        self.root_dir = root_dir
        self.field_id = field_id
    def __call__(self, instance, filename):
        # See this functions documentation in django > FileField for more details.
        # This function must have two arguments: instance and filename.
        # get the extension of the incoming/browsed file
        ext = filename.split('.')[-1]
        # create a filename from instance id and timestamp
        path = self.root_dir + '{}_{}.{}'.format(instance.id, self.field_id, ext)
        return path


#    Categories
# ---------------------------------------------------------------------------- #

class Category(models.Model):
    name = models.CharField(max_length=100)
    hidden = models.BooleanField(default=False)
    # add a display order dropdown field
    display_order = models.PositiveSmallIntegerField(default=0)
    def __str__(self):
        return self.name


#    Tags
# ---------------------------------------------------------------------------- #

class Tag(models.Model):
    name = models.CharField(max_length=100)
    hidden = models.BooleanField(default=False)
    def __str__(self):
        return self.name


#    References
# ---------------------------------------------------------------------------- #

class Reference(models.Model):
    name = models.CharField(max_length=200)
    url = models.URLField()
    # add a select from choices field to select the type of reference
    category = models.CharField(max_length=100, choices=[('page', 'page'), ('scientific article', 'scientific article'), ('video', 'video'), ('wikipedia', 'wikipedia')], default='page')
    def __str__(self):
        return self.name


#    Posts
# ---------------------------------------------------------------------------- #

class Post(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    categories = models.ManyToManyField(Category)
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    publication_date = models.DateField()
    abstract = models.TextField(blank=True)
    body = models.TextField()
    image_1 = models.ImageField(upload_to=uploadPath(POST_IMAGE_DIR, '1'), blank=True)
    image_2 = models.ImageField(upload_to=uploadPath(POST_IMAGE_DIR, '2'), blank=True)
    image_3 = models.ImageField(upload_to=uploadPath(POST_IMAGE_DIR, '3'), blank=True)
    image_4 = models.ImageField(upload_to=uploadPath(POST_IMAGE_DIR, '4'), blank=True)
    image_5 = models.ImageField(upload_to=uploadPath(POST_IMAGE_DIR, '5'), blank=True)
    image_6 = models.ImageField(upload_to=uploadPath(POST_IMAGE_DIR, '6'), blank=True)
    main_image_index = models.CharField(max_length=1, choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")], default="1")
    # if the foreign key belongs to another app (not the best practice for app independence), use the app-name before the model-name and put both in quotes.
    organization = models.ForeignKey('base.Organization', on_delete=models.SET_NULL, null=True, blank=True)
    featured = models.BooleanField(default=False)
    references = models.ManyToManyField(Reference, blank=True)
    time_created = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

