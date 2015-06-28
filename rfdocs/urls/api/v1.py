#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from rfdocs import views_api

version_detail = views_api.RFLibraryViewSet.as_view({
    'get': 'retrieve'
})

library_list = views_api.RFLibraryViewSet.as_view({'get': 'list'})

library_version_detail = views_api.RFLibraryVersionViewSet.as_view({'get': 'retrieve'})

keyword_detail = views_api.RFKeywordViewSet.as_view({'get': 'retrieve'})

tag_detail = views_api.RFTagViewSet.as_view({'get': 'retrieve'})

urlpatterns = format_suffix_patterns(
    patterns('rfdocs.views_api',
             url(r'^$', library_list, name='rfversion-list'),
             url(r'^tag/(?P<slug>[-\w]+)/$', tag_detail, name='rftag_detail_api'),
             url(r'^(?P<slug>[-\w.]+)/$', version_detail, name='rflibrary_detail_api'),
             url(r'^(?P<library_slug>[-\w.]+)/(?P<slug>[-\w.]+)/$', library_version_detail,
                 name='rflibraryversion_detail_api'),
             url(r'^(?P<library_slug>[-\w.]+)/(?P<version_slug>[-\w.]+)/(?P<name>[-\w\s]+)/$',
                 keyword_detail,
                 name='rfkeyword_detail_api'),
             )
)
