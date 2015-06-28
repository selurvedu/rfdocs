#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import unicodedata

from django.template.defaultfilters import stringfilter, register
from django.utils import six
from django.utils.functional import allow_lazy
from django.utils.safestring import mark_safe


def _slugify(value):
    """
    django.utils.text.slugify that allows to use dot(.) in a slug field.

    This method is a copy of django.utils.text.slugify.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\.^\w\s-]', '', value).strip().lower()
    return mark_safe(re.sub('[-\s]+', '-', value))
_slugify = allow_lazy(_slugify, six.text_type)


@register.filter(is_safe=True)
@stringfilter
def slugify_allow_dots(value):
    return _slugify(value)
