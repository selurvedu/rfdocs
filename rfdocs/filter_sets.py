#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django_filters import widgets, ChoiceFilter, FilterSet

from .models import (RFLibrary, RFLibraryVersion, RFKeyword,
                     RFTag)

ALL = ('', 'All')


class AllValuesFilter(ChoiceFilter):
    """
    This is overridden django_filters.AllValuesFilter that appends 'All' to choices.
    """
    @property
    def field(self):
        qs = self.model._default_manager.distinct()
        qs = qs.order_by(self.name).values_list(self.name, flat=True)
        self.extra['choices'] = tuple([ALL, ] + [(o, o) for o in qs])
        return super(AllValuesFilter, self).field


# Usage of '.distinct' eliminates duplicate rows from the query results.
# As per Django docs, passing field names to '.distinct' is supported by PostgreSQL only.
# https://docs.djangoproject.com/en/1.5/ref/models/querysets/

class RFLibraryFilter(FilterSet):
    name = AllValuesFilter(widget=widgets.LinkWidget)
    codename = AllValuesFilter(widget=widgets.LinkWidget)

    class Meta:
        model = RFLibrary
        fields = ['name', 'codename', ]

    def __init__(self, *args, **kwargs):
        super(RFLibraryFilter, self).__init__(*args, **kwargs)
        # need only unique libraries names
        versions_list = RFLibraryVersion.objects.order_by('name').\
            values_list('name', flat=True).distinct('name')
        versions_choices = [(s, s) for s in versions_list]
        versions_choices.insert(0, ALL)
        ver = ChoiceFilter(
            name="version__name",
            choices=tuple(versions_choices),
            widget=widgets.LinkWidget,
        )
        self.filters['versions'] = ver


class RFLibraryVersionFilter(FilterSet):
    name = AllValuesFilter(widget=widgets.LinkWidget)
    status = AllValuesFilter(widget=widgets.LinkWidget)

    class Meta:
        model = RFLibraryVersion
        fields = ['name', 'status', 'tags', ]

    def __init__(self, *args, **kwargs):
        super(RFLibraryVersionFilter, self).__init__(*args, **kwargs)
        tags_list = RFTag.objects.order_by('name').values_list('name', flat=True)
        tags_choices = [(s, s) for s in tags_list]
        tags_choices.insert(0, ALL)
        libraries_list = RFLibrary.objects.order_by('name').\
            values_list('name', flat=True)
        libraries_choices = [(s, s) for s in libraries_list]
        libraries_choices.insert(0, ALL)
        tag = ChoiceFilter(
            name="tags__name",
            choices=tuple(tags_choices),
            widget=widgets.LinkWidget,
        )
        lib = ChoiceFilter(
            name="library__name",
            choices=tuple(libraries_choices),
            widget=widgets.LinkWidget,
        )
        self.filters['tags'] = tag
        self.filters['libraries'] = lib


class RFKeywordFilter(FilterSet):
    name = AllValuesFilter(widget=widgets.LinkWidget)

    class Meta:
        model = RFKeyword
        fields = ['name', ]

    def __init__(self, *args, **kwargs):
        super(RFKeywordFilter, self).__init__(*args, **kwargs)
        qs = RFKeyword.objects.all().prefetch_related('version')
        versions_list = qs.order_by('version__name').\
            values_list('version__name', flat=True).distinct('version__name')
        versions_choices = [(s, s) for s in versions_list]
        versions_choices.insert(0, ALL)
        libraries_list = qs.order_by('version__library__name').values_list(
            'version__library__name', flat=True).distinct('version__library__name')
        libraries_choices = [(s, s) for s in libraries_list]
        libraries_choices.insert(0, ALL)
        ver = ChoiceFilter(
            name="version__name",
            choices=tuple(versions_choices),
            widget=widgets.LinkWidget,
        )
        lib = ChoiceFilter(
            name="version__library__name",
            choices=tuple(libraries_choices),
            widget=widgets.LinkWidget,
        )
        self.filters['libraries'] = lib
        self.filters['versions'] = ver


class RFTagFilter(FilterSet):
    """
    Provides filtering capabilities for ListView view of RFTag model.
    """

    name = AllValuesFilter(label='Name', widget=widgets.LinkWidget)

    class Meta:
        model = RFTag
        fields = ['name', ]

    def __init__(self, *args, **kwargs):
        super(RFTagFilter, self).__init__(*args, **kwargs)
        qs = RFLibraryVersion.objects.prefetch_related('library')

        versions_list = qs.order_by('name').values_list('name', flat=True).distinct('name')
        versions_choices = [(s, s) for s in versions_list]
        versions_choices.insert(0, ALL)
        libraries_list = qs.order_by('library__name').\
            values_list('library__name', flat=True).distinct('library__name')
        libraries_choices = [(s, s) for s in libraries_list]
        libraries_choices.insert(0, ALL)
        ver = ChoiceFilter(
            name="versions__name",
            choices=tuple(versions_choices),
            widget=widgets.LinkWidget,
        )
        lib = ChoiceFilter(
            name="versions__library__name",
            choices=tuple(libraries_choices),
            widget=widgets.LinkWidget,
        )
        self.filters['libraries'] = lib
        self.filters['versions'] = ver
