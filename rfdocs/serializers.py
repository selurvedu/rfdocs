#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rest_framework import serializers
from rest_framework.reverse import reverse

from rfdocs.models import (RFLibrary, RFKeyword,
                           RFLibraryVersion, RFTag)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer which takes an additional `field` argument that
    controls which fields should be displayed.
    """
    def __init__(self, *args, **kwargs):
        default_fields = kwargs.pop('fields', [])
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        existing = set(self.fields.keys())
        if self.instance:
            if 'request' in self.context:
                requested_fields = self.context['request'].GET.getlist('field', [])
                default_fields.extend([f for f in requested_fields if f in existing])
        allowed = set(default_fields)
        if allowed:
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ConsecutiveHyperlinkedField(serializers.HyperlinkedIdentityField):
    """
    Inheritor of serializers.HyperlinkedIdentityField serializer that allows to define a tuple of
    lookup fields, where field can be dot-notated string.
    """
    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop('lookup_fields', None)
        super(ConsecutiveHyperlinkedField, self).__init__(*args, **kwargs)

    @staticmethod
    def getattr_consecutive(obj, dot_notated_string):
        """
        Allows dot-notated strings to be passed to `getattr`
        """
        return reduce(getattr, dot_notated_string.split('.'), obj)

    def get_url(self, obj, view_name, request, url_format):
        args = ()
        if self.lookup_fields:
            args = (self.getattr_consecutive(obj, arg) for arg in self.lookup_fields)
        return reverse(view_name, args=args, request=request, format=url_format)


class RFKeywordSerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsModelSerializer):
    version = ConsecutiveHyperlinkedField(
        lookup_fields=('version.library.slug', 'version.slug',),
        view_name='rflibraryversion_detail_api',
    )

    library = ConsecutiveHyperlinkedField(
        lookup_fields=('version.library.slug',),
        view_name='rflibrary_detail_api',
    )

    url = ConsecutiveHyperlinkedField(
        lookup_fields=('version.library.slug', 'version.slug', 'name',),
        view_name='rfkeyword_detail_api',
    )

    class Meta:
        model = RFKeyword
        fields = ('name', 'url', 'version', 'arguments', 'documentation', 'library')


class RFLibraryVersionSerializer(serializers.HyperlinkedModelSerializer,
                                 DynamicFieldsModelSerializer):
    def __init__(self, *args, **kwargs):
        super(RFLibraryVersionSerializer, self).__init__(*args, **kwargs)
        if 'request' in self.context:
            requested_fields = self.context['request'].GET.getlist('keyword_field', [])
            allowed = set(RFKeywordSerializer.Meta.fields).intersection(set(requested_fields))
            if allowed:
                self.fields['keywords'] = RFKeywordSerializer(
                    fields=list(allowed),
                    many=True,
                    context={'request': self.context['request']}
                )

    library = serializers.StringRelatedField()

    library_url = ConsecutiveHyperlinkedField(
        lookup_fields=('library.slug', ),
        view_name='rflibrary_detail_api'
    )

    url = ConsecutiveHyperlinkedField(
        lookup_fields=('library.slug', 'slug'),
        view_name='rflibraryversion_detail_api',
    )

    keywords = RFKeywordSerializer(
        many=True,
        fields=['name', 'url', 'arguments']
    )

    class Meta:
        model = RFLibraryVersion
        fields = ['name', 'library', 'library_url', 'slug', 'url', 'source_url', 'keywords', 'status',
                  'date_added', 'date_modified', 'date_deprecate']


class RFLibrarySerializer(serializers.HyperlinkedModelSerializer, DynamicFieldsModelSerializer):
    def __init__(self, *args, **kwargs):
        super(RFLibrarySerializer, self).__init__(*args, **kwargs)
        if 'request' in self.context:
            requested_fields = self.context['request'].GET.getlist('version_field', [])
            allowed = set(RFLibraryVersionSerializer.Meta.fields).intersection(set(requested_fields))
            if allowed:
                self.fields['versions'] = RFLibraryVersionSerializer(
                    fields=list(allowed),
                    many=True,
                    context={'request': self.context['request']}
                )

    url = serializers.HyperlinkedIdentityField(
        view_name='rflibrary_detail_api',
        lookup_field='slug'
    )

    versions = RFLibraryVersionSerializer(
        fields=['name', 'url'],
        many=True
    )

    class Meta:
        model = RFLibrary
        fields = ('name', 'slug', 'url', 'versions')
        lookup_field = 'slug'


class RFTagSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        lookup_field='slug',
        view_name='rftag_detail_api',
    )

    versions = RFLibraryVersionSerializer(fields=('name', 'url'))

    class Meta:
        model = RFTag
        fields = ('name', 'slug', 'url', 'versions')
