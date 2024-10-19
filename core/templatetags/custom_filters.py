# core/templatetags/cloudinary_filters.py

from django import template

register = template.Library()

@register.filter(name='replace_cloudinary_url')
def replace_cloudinary_url(url):
    """
    Replace the URL prefix to make it downloadable.
    """
    
    return url.replace("image/upload/", "image/upload/fl_attachment:")
