from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def split(value,split_string):
  import unicodedata
  value = unicodedata.normalize('NFKD', value).encode('ascii','ignore')
  return value.split(split_string)[-1]
