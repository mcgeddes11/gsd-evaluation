import nh3

_ALLOWED_TAGS = {
    "p", "br", "h1", "h2","h3"
    "strong","em","u","s",
    "ul","ol","li",
    "blockquote","pre","code",
    "a","span",
    "img", # for uploaded images
    "iframe" # for video embeds
}

_ALLOWED_ATTRIBUTES = {
    "a": {"href", "target"},
    "p": {"class"},
    "span": {"class"},
    "li": {"class"},
    "code": {"class"},
    "pre": {"class"},
    "img": {"src","alt","width","height","class"},
    "iframe": {"src","width","height","frameborder","allowfullscreen","allow","class"}
}

def sanitize_html(html: str) -> str:
    """ Utility method for sanitizing HTML for posts """
    return nh3.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES, link_rel=None)