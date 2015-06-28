#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib import admin
from django.conf.urls import patterns, include, url

from rfdocs import views
from rfdocs.mixins import tools

admin.autodiscover()

handler404 = views.NotFound404.raiseError()
handler500 = views.ApplicationError500.raiseError()

urlpatterns = patterns('',
                       url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       url(r'^admin/', include(admin.site.urls)),
                       )

if not settings.DEBUG:
    admin_url = tools.get_env_variable('DJANGO_ADMIN_URL', fail_to='admin')
    urlpatterns = patterns('',
                           url(r'^%s/doc/' % admin_url, include('django.contrib.admindocs.urls')),
                           url(r'^%s/' % admin_url, include(admin.site.urls)),
                           )
try:
    import mysite.urls
    urlpatterns += patterns('', url(r'', include(mysite.urls), name='mysite'))
except ImportError:
    pass

urlpatterns += patterns('rfdocs.views',
                        url(r'^$', views.HomeView.as_view(), name='home'),
                        url(r'^browse/$', views.BrowseView.as_view(), name='browse'),
                        url(r'^dataset/load(?P<params>.*)$',
                            views.LoadLibrariesView.as_view(),
                            name='dataset_load'))

# It would be better to set url regex '^browse' here for all views,
# but because the urlconf is nested, it causes
# problems in views with 'reverse'.
# Thus all regex patterns are inside corresponding url modules, not here.
urlpatterns += patterns('',
                        url(r'', include('rfdocs.urls.keywords'), name='keywords'),
                        url(r'', include('rfdocs.urls.versions'), name='versions'),
                        url(r'', include('rfdocs.urls.libraries'), name='libraries'),
                        url(r'^filter/', include('rfdocs.urls.filters'), name='filters'),
                        )

urlpatterns += patterns('',
                        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                         {'document_root': settings.MEDIA_ROOT}),
                        )

urlpatterns += patterns('',
                        url(r'^api/', include('rfdocs.urls.api.urls'), name='api'),
                        )
