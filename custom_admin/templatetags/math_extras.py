# custom_admin/templatetags/math_extras.py
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiplies the given value by the argument.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
