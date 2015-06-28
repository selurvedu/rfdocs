#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rfdocs.views import RFLibraryVersionDetailView


library_version_detail_view = url(
    r'^browse/(?P<library_slug>[-\w.]+)/(?P<slug>[-\w.]+)/$',
    vary_on_headers('X-Requested-With')(cache_page(86400)(RFLibraryVersionDetailView.as_view())),
    name='rflibraryversion_detail'
)

urlpatterns = patterns('django.views.generic.detail', library_version_detail_view)
