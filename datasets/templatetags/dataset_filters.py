"""Custom template filters for datasets app."""
from django import template

register = template.Library()


@register.filter
def replace_char(value, arg):
    """Replace a character with another character.
    
    Usage: {{ value|replace_char:"_" }}
    This will replace underscores with spaces.
    Example: {{ "hello_world"|replace_char:"_" }} → "hello world"
    """
    if not arg:
        return value
    
    return str(value).replace(arg, ' ')


@register.filter
def dict_lookup(dict_obj, key):
    """Get a value from a dictionary using a key.
    
    Usage: {{ dict|dict_lookup:key_name }}
    Example: {{ row|dict_lookup:col_name }} to access row[col_name]
    """
    if isinstance(dict_obj, dict):
        return dict_obj.get(key, '')
    return ''
