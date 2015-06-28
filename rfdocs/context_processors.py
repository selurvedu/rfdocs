#!/usr/bin/env python

# in settings.py
# TEMPLATE_CONTEXT_PROCESSORS = (
#     ...
#     'rfdocs.context_processors.debug',
# )
# in template
# {% if DEBUG %}

from django.conf import settings


def debug(context):
    return {'SETTINGS_DEBUG': settings.DEBUG}
