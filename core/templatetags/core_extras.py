from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def matches(value, arg):
    """Compares two values for equality, converting to string to handle type differences."""
    return str(value) == str(arg)
