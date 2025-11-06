from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter pro získání hodnoty ze slovníku podle klíče."""
    if dictionary is None:
        return None
    return dictionary.get(key)
