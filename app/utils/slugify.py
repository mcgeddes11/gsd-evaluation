import re
from slugify import slugify

def generate_slug(title):
    """
    Generate a URL-friendly slug from a post title

    Args:
        title: String to slugify

    Returns:
        Slugified text (alphanumeric + hyphens, max length 255 chars)
    """
    if not title:
        return "untitled"

    return slugify(title, max_length=255)


def validate_slug(slug):
    if not slug or len(slug) > 255:
        return False
    return bool(re.match(r'[a-z0-9_-]{1,255}$', slug))