#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import url, patterns
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rfdocs.views import RFKeywordDetailView


keyword_detail_view = url(
    r'^browse/(?P<library_slug>[-\w.]+)/(?P<version_slug>[-\w.]+)/(?P<slug>[-\w\s]+)/$',
    vary_on_headers('X-Requested-With')(cache_page(86400)(RFKeywordDetailView.as_view())),
    name='rfkeyword_detail'
)

urlpatterns = patterns('django.views.generic.detail', keyword_detail_view)
