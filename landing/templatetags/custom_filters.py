from django import template

register = template.Library()

@register.filter(name='split')
def split_filter(value, arg):
    """Split a string by the given separator."""
    return value.split(arg)

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='add_val')
def add_val(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0
