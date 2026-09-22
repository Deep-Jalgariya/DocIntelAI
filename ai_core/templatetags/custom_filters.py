from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def add_val(value, arg):
    """Add a numeric value."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value
