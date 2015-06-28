#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.metadata import SimpleMetadata
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView

from rfdocs.models import (RFLibrary, RFKeyword, RFLibraryVersion, RFTag)
from rfdocs.serializers import (RFLibrarySerializer, RFKeywordSerializer,
                                RFLibraryVersionSerializer, RFTagSerializer)

logger = logging.getLogger(name=__name__)


class RootView(APIView):
    """
    Robot Framework Documentation Manager API
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        api_versions = ('v1',)
        abs_uri = request.build_absolute_uri()
        return Response(dict([(v, '%s%s' % (abs_uri, v)) for v in api_versions]))

# def get_metadata_class(metadata=None):
#     metadata = metadata or {}
#
#     class CustomMetadata(SimpleMetadata):
#         def determine_metadata(self, request, view):
#             data = super(CustomMetadata, self).determine_metadata(request, view)
#             data.update(metadata)
#             print "data: ", data
#             return data
#
#     return CustomMetadata


class RFLibraryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Robot Framework Documentation Manager API.
    """
    lookup_field = 'slug'
    permission_classes = (AllowAny,)
    queryset = RFLibrary.objects.prefetch_related('versions__keywords', 'versions__tags')
    serializer_class = RFLibrarySerializer
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)


class RFLibraryVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List of all libraries.
    """
    # metadata_class = get_metadata_class(metadata={'name': 'List of libraries'})

    permission_classes = (AllowAny,)
    queryset = RFLibraryVersion.objects.all()
    serializer_class = RFLibraryVersionSerializer

    def get_object(self, queryset=queryset):
        filter_kwargs = {
            'library__slug': self.kwargs['library_slug'],
            'slug': self.kwargs['slug']
        }
        obj = get_object_or_404(queryset, **filter_kwargs)
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj


class RFKeywordViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    slug_field = 'name'
    serializer_class = RFKeywordSerializer
    # renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)

    def get_object(self, queryset=None):
        filter_kwargs = {
            'version__library__slug': self.kwargs['library_slug'],
            'version__slug': self.kwargs['version_slug'],
            'name': self.kwargs['name']
        }
        obj = get_object_or_404(self.get_queryset(), **filter_kwargs)
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        vals = self.request.QUERY_PARAMS.get('values', None)
        if vals is not None:
            vals = [val.strip() for val in vals.split(',')]
            self.serializer_class.Meta.fields = vals
        return RFKeyword.objects.filter(
            version__library__slug=self.kwargs['library_slug'],
            version__slug=self.kwargs['version_slug']
        )


class RFTagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = RFTag.objects.all()
    serializer_class = RFTagSerializer
