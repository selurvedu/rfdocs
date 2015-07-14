#!/usr/bin/env python

import os
import sys

settings_file = os.environ.get("DJANGO_SETTINGS_MODULE")
# Default value of DJANGO_SETTINGS_MODULE is set in rfdocset/wsgi.py
if settings_file == "rfdocset.settings":
    settings_file = "rfdocset.settings.dev"


class SettingsModuleWrapper(object):
    def __init__(self, mod):
        wrapped = __import__(mod, globals=globals(),locals=locals(), fromlist="*")
        try:
            attrlist = wrapped.__all__
        except AttributeError:
            attrlist = dir(wrapped)
        for attr in [a for a in attrlist if '__' not in a]:
            setattr(self, attr, getattr(wrapped, attr))

sys.modules[__name__] = SettingsModuleWrapper(settings_file)
