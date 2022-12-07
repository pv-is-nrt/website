import markdown

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def markdown_to_html(markdown_text):
    return markdown.markdown(markdown_text, extensions=['markdown.extensions.fenced_code'])