#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include

from rfdocs import views_api


urlpatterns = patterns('',
                       url(r'^$', views_api.RootView.as_view(), name='api_root'),
                       url(r'^v1/', include('rfdocs.urls.api.v1')),
                       url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')))
