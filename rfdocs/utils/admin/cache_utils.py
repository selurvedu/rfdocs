#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import messages
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from rfdocs.mixins.memcached_helper import clear_dataset_cache


def invalidate_view_cache(obj, request, target):
    if target is not None:
        res = target.invalidate_cache()
        if not res:
            obj.message_user(request, 'The item is not cached: %s' % target, level=messages.WARNING)
            return None  # Redirect or Response or None
        obj.message_user(request, 'Successfully expired cache for item: %s' % target)
    return None  # Redirect or Response or None


def invalidate_children_view_cache(obj, request, target, method, message_success=None,
                                   message_fail=None):
    success = 'Successfully expired cache for these items' or message_success
    fail = 'These items were not cached' or message_fail
    cleared = []
    not_cleared = []
    if target is not None:
        res = getattr(target, method)()
        for k, v in res.iteritems():
            if v:
                cleared.append(k)
            else:
                not_cleared.append(k)
        if cleared:
            list_items = _('<ul>%s</ul>') % ' '.join(['<li>%s</li>' % el for el in cleared])
            final_message = '%s: %s' % (success, list_items)
            obj.message_user(request, mark_safe(final_message), level=messages.SUCCESS)
        if not_cleared:
            list_items = _('<ul>%s</ul>') % " ".join(['<li>%s</li>' % el for el in not_cleared])
            final_message = '%s: %s' % (fail, list_items)
            obj.message_user(request, mark_safe(final_message), level=messages.WARNING)
    return None  # Redirect or Response or None


def invalidate_dataset_cache(model_admin, request, dummy_obj):
    res = clear_dataset_cache()
    model_admin.message_user(request, res, level=messages.INFO)
    return None  # Redirect or Response or None
invalidate_dataset_cache.short_description = 'Invalidate Dataset Cache'


def invalidate_entity_cache(model_admin, request, entity=None):
    return invalidate_view_cache(model_admin, request, entity)
invalidate_entity_cache.short_description = 'Invalidate Cache'


def invalidate_versions_cache(model_admin, request, entity=None):
    return invalidate_children_view_cache(model_admin, request, entity,
                                          'invalidate_versions_cache')
invalidate_versions_cache.short_description = 'Invalidate Libraries Cache'


def invalidate_keywords_cache(model_admin, request, entity=None):
    return invalidate_children_view_cache(model_admin, request, entity, 'invalidate_keywords_cache')
invalidate_keywords_cache.short_description = 'Invalidate Keywords Cache'