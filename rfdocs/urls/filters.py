#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers


from rfdocs.views import (RFTagListViewFilter, RFLibraryListViewFilter,
                          RFLibraryVersionListViewFilter)

one_day = 86400

libraries_list_view_filter = url(
    r'^libraries/',
    vary_on_headers('X-Requested-With')(cache_page(one_day)(RFLibraryListViewFilter.as_view())),
    name='libraries_list_filter'
)

versions_list_view_filter = url(
    r'^versions/',
    vary_on_headers('X-Requested-With')(cache_page(one_day)(RFLibraryVersionListViewFilter.as_view())),
    name='versions_list_filter'
)

tags_list_view_filter = url(
    r'^tags/',
    vary_on_headers('X-Requested-With')(cache_page(one_day)(RFTagListViewFilter.as_view())),
    name='tags_list_filter'
)
urlpatterns = patterns('',
                       versions_list_view_filter,
                       libraries_list_view_filter,
                       tags_list_view_filter)

