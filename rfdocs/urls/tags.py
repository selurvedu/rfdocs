#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

from rfdocs.views import RFTagDetailView


tag_detail_view = url(r'^(?P<slug>[-\w]+)/$', RFTagDetailView.as_view(),
                      name='robot_framework_tag_detail')

urlpatterns = patterns('django.views.generic.detail', tag_detail_view)
