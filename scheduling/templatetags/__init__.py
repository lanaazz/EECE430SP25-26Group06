from django import template

register = template.Library()


@register.filter
def has_key(dictionary, key):
    """Check if a dictionary has the given key."""
    return key in dictionary


@register.filter
def dict_get(dictionary, key):
    """Get a value from a dictionary by key."""
    return dictionary.get(key, [])
