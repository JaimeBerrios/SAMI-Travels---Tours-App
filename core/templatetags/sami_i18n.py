from django import template
from django.utils.translation import get_language


register = template.Library()


@register.simple_tag
def bilingual(spanish, english, language=None):
    selected = (language or get_language() or "es").lower()
    return english if selected.startswith("en") else spanish
