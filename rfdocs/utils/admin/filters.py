#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.contrib.admin import SimpleListFilter
from django.db.models import Count
from django.utils.translation import ugettext as _


class CountItemsListFilter(SimpleListFilter):
    """
    Filters items by foreign key count.

    This is base class that should not be used directly.
    """
    title = _('number of items')

    parameter_name = 'items'
    lookup_dict = {'0_0': _('0'),
                   '1_20': _('1-20'),
                   '21_50': _('21-50'),
                   '51_100': _('51-100'),
                   '101': _('More than 100')}
    lookup_values = OrderedDict(sorted(lookup_dict.items(), key=lambda v: v[1]))

    def lookups(self, request, model_admin):
        return tuple(zip(self.lookup_values.keys(), self.lookup_values.values()))

    def queryset(self, request, queryset):
        for k, v in self.lookup_values.iteritems():
            if self.value() == k:
                r = k.split('_')
                if len(r) == 2:
                    return queryset.annotate(my_items_count=Count(self.parameter_name)).\
                        filter(my_items_count__range=(int(r[0]), int(r[1])))
                elif len(r) == 1:
                    return queryset.annotate(my_items_count=Count(self.parameter_name)).\
                        filter(my_items_count__gt=int(r[0]))


class CountVersionsListFilter(CountItemsListFilter):
    title = _('number of versions')
    parameter_name = 'versions'


class CountKeywordsListFilter(CountItemsListFilter):
    title = _('number of keywords')
    parameter_name = 'keywords'
