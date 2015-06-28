#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from django import template
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.simple_tag
def SITE_NAME():
    return Site.objects.get_current().domain


@register.simple_tag
def COPYRIGHT_DATE():
    start_year = 2013
    year = datetime.datetime.now().year
    if year == start_year:
        return unicode(year)
    elif year > start_year:
        return u'%s&ndash;%s' % (start_year, year)
    return unicode(year)


@register.simple_tag
def AUTHOR():
    return _("Andriy Hrytskiv")
