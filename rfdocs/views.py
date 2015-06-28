#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import json
import functools
import logging

from django.conf import settings
from django.core.cache import caches
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import TemplateView

from braces.views import JSONResponseMixin
from django_filters.views import FilterView

from rfdocs.filter_sets import (RFLibraryFilter, RFKeywordFilter, RFTagFilter,
                                RFLibraryVersionFilter)
from rfdocs.models import (RFLibrary, RFKeyword, RFLibraryVersion, RFTag)
from rfdocs.templatetags.rfdocs_tags import generate_node_key

PAGINATE_BY = settings.RFDOCS.get('PAGINATE_BY', 25)

logger = logging.getLogger(name=__name__)


def select_template(template_ajax, template_not_ajax):
    """
    Sets template name based on type of the request.

    Can be used as a decorator of `get_template_names` method of a generic class-based views.
    """
    def wrapper(func):
        @functools.wraps(func)
        def worker(self):
            if self.request.is_ajax():
                self.template_name = template_ajax
            else:
                self.template_name = template_not_ajax
            return func(self)
        return worker
    return wrapper


class ErrorHandler(TemplateView):
    @classmethod
    def raiseError(cls):
        v = cls.as_view()

        def view(request):
            r = v(request)
            if isinstance(r, HttpResponseNotAllowed):
                json_context = json.dumps(
                    {u"errors": [u"Improperly formatted request", ]},
                    cls=DjangoJSONEncoder,
                )
                return HttpResponseNotAllowed(['GET', 'POST', ], json_context)
            r.render()
            return r
        return view


class NotFound404(ErrorHandler):
    @select_template('404ajax.html', '404.html')
    def get_template_names(self):
        return [self.template_name, ]


class ApplicationError500(ErrorHandler):
    @select_template('500ajax.html', '500.html')
    def get_template_names(self):
        return [self.template_name, ]


class HomeView(TemplateView):
    template_name = 'rfdocs/base/base.html'


class BrowseView(TemplateView):
    template_name = 'rfdocs/base/browse.html'


class HandleBadRequestJSONResponseMixin(JSONResponseMixin):
    error_response_dict = {u"errors": [u"Improperly formatted request", ]}
    http_resp_class = HttpResponseBadRequest

    def render_bad_request_response(self, error_dict=None):
        if error_dict is None:
            error_dict = self.error_response_dict
        json_context = json.dumps(
            error_dict,
            cls=DjangoJSONEncoder,
            **self.get_json_dumps_kwargs()
        )
        return self.http_resp_class(json_context, content_type=self.get_content_type())


class LoadLibrariesView(HandleBadRequestJSONResponseMixin, ListView):
    model = RFLibrary
    context_object_name = 'libraries_list'
    content_type = 'application/json'

    _cache_key_prefix = 'data_set'
    _cache_time = 604800  # 1 week

    def get_request_json_params(self):
        if not self.request.method == 'GET':
            self.error_response_dict = {u"errors": [u"Method not allowed", ]}
            self.http_resp_class = HttpResponseNotAllowed
            return None
        try:
            return self.request.GET.getlist('library')
        except ValueError:
            return None

    @staticmethod
    def _update_context(context):
        libraries = []
        for l in context['libraries_list']:
            library = {
                'children': [],
                'href': l.get_absolute_url(),
                'iconClass': 'icon-folder-close',
                'isVersion': True,
                'isFolder': True,
                'key': generate_node_key(l.name),
                'title': l.name,
                'tooltip': unicode(l),
            }
            for v in l.versions.not_draft():
                tags = v.tags_as_list
                version = {
                    'children': [],
                    'href': v.get_absolute_url(),
                    'hideCheckbox': True,
                    'iconClass': 'icon-folder-close-alt',
                    'isFolder': True,
                    'isLibrary': True,
                    'key': generate_node_key(l.name, v.name),
                    'status': v.status,
                    'tags': tags,
                    'title': v.name,
                    'tooltip': unicode(v),
                }
                for k in v.keywords.all():
                    keyword = {
                        'api_href': k.get_api_url(),
                        'href': k.get_absolute_url(),
                        'hideCheckbox': True,
                        'iconClass': 'icon-key',
                        'title': k.name,
                        'key': generate_node_key(l.name, v.name, k.name),
                        'tooltip': unicode(k),
                    }
                    version['children'].append(keyword)
                library['children'].append(version)
            libraries.append(library)
        return libraries

    def _build_cache_key(self):
        try:
            key = ':'.join([v for v in self.request_json_params])
            return '%s:%s:%s' % (self._cache_key_prefix, hashlib.md5(key).hexdigest(),
                                 len(self.request_json_params))
        except Exception as err:
            logger.exception(err)
            return '%s:%s' % (self._cache_key_prefix, hashlib.md5('').hexdigest())

    def dispatch(self, request, *args, **kwargs):
        self.request_json_params = self.get_request_json_params()
        if self.request_json_params is None:
            return self.render_bad_request_response()
        return super(LoadLibrariesView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LoadLibrariesView, self).get_context_data(**kwargs)
        cached_key = self._build_cache_key()
        dataset_cache = caches['dataset']
        cached_context = dataset_cache.get(cached_key)
        if cached_context:
            return cached_context
        objects = RFLibrary.objects.all()
        if self.request_json_params:
            context['libraries_list'] = objects.filter(name__in=self.request_json_params). \
                prefetch_related('versions__keywords', 'versions__tags')
            updated_context = self._update_context(context)
            dataset_cache.set(cached_key, updated_context, self._cache_time)
            return updated_context
        context['libraries_list'] = objects.prefetch_related('versions__keywords',
                                                             'versions__tags')
        updated_context = self._update_context(context)
        dataset_cache.set(cached_key, updated_context, self._cache_time)
        return updated_context

    def render_to_response(self, context, **response_kwargs):
        return self.render_json_response(context, **response_kwargs)


class RFLibraryDetailView(DetailView):
    queryset = RFLibrary.objects.prefetch_related('versions')

    @select_template('rfdocs/library/detail/ajax.html', 'rfdocs/library/detail/detail.html')
    def get_template_names(self):
        return [self.template_name, ]

    def get_context_data(self, **kwargs):
        context = super(RFLibraryDetailView, self).get_context_data(**kwargs)
        qs = self.queryset.filter(slug=context['rflibrary'].slug)
        context.update(qs.aggregate(number_of_keywords=Count('versions__keywords')))
        context.update(qs.aggregate(number_of_versions=Count('versions')))
        return context


class RFLibraryListViewFilter(FilterView):
    context_object_name = 'libraries_list'
    filterset_class = RFLibraryFilter
    paginate_by = PAGINATE_BY

    @select_template('rfdocs/library/list/ajax.html', 'rfdocs/library/list/filter.html', )
    def get_template_names(self):
        return [self.template_name, ]


class RFLibraryVersionDetailView(DetailView):
    queryset = RFLibraryVersion.objects.not_draft()

    @select_template('rfdocs/version/detail/ajax.html', 'rfdocs/version/detail/detail.html')
    def get_template_names(self):
        return [self.template_name, ]

    def get_queryset(self):
        return self.queryset.select_related('library').prefetch_related('keywords', 'tags').\
            filter(library__slug=self.kwargs['library_slug'])


class RFLibraryVersionListViewFilter(FilterView):
    context_object_name = 'versions_list'
    filterset_class = RFLibraryVersionFilter
    paginate_by = PAGINATE_BY

    @select_template('rfdocs/version/list/ajax.html', 'rfdocs/version/list/filter.html', )
    def get_template_names(self):
        return [self.template_name, ]


class RFKeywordDetailView(DetailView):
    slug_field = 'name'
    queryset = RFKeyword.objects.select_related('version')

    @select_template('rfdocs/keyword/detail/ajax.html', 'rfdocs/keyword/detail/detail.html')
    def get_template_names(self):
        return [self.template_name, ]

    def get_queryset(self):
        return self.queryset.filter(
            version__library__slug=self.kwargs['library_slug'],
            version__slug=self.kwargs['version_slug']
        )


class RFKeywordListViewFilter(FilterView):
    context_object_name = 'keywords_list'
    filterset_class = RFKeywordFilter
    paginate_by = PAGINATE_BY

    @select_template('rfdocs/keyword/list/ajax.html', 'rfdocs/keyword/list/filter.html', )
    def get_template_names(self):
        return [self.template_name, ]


class RFTagDetailView(DetailView):
    model = RFTag

    @select_template('rfdocs/tag/detail/ajax.html', 'rfdocs/tag/detail/detail.html')
    def get_template_names(self):
        return [self.template_name, ]


class RFTagListViewFilter(FilterView):
    context_object_name = 'tags_list'
    filterset_class = RFTagFilter
    paginate_by = PAGINATE_BY

    @select_template('rfdocs/tag/list/ajax.html', 'rfdocs/tag/list/filter.html', )
    def get_template_names(self):
        return [self.template_name, ]
