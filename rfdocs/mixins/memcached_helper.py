#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from django.core.cache import get_cache, cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpRequest
from django.utils.cache import get_cache_key


def expire_view_cache(view_name, args=(), namespace=None, key_prefix=None, method="GET"):
    """
    This function allows you to invalidate any view-level cache.
        view_name: view function you wish to invalidate or it's named url pattern
        args: any arguments passed to the view function
        namepace: optioal, if an application namespace is needed
        key prefix: for the @cache_page decorator for the function (if any)

    Source: http://stackoverflow.com/questions/2268417/expire-a-view-cache-in-django

    Example:
        from django.db.models.signals import post_save
        from blog.models import Entry

        def invalidate_blog_index(sender, **kwargs):
            invalidate_view_cache("blog")
        post_save.connect(invalidate_portfolio_index, sender=Entry)
    """
    # create a fake request object
    request = HttpRequest()
    request.method = method
    request.META = {'HTTP_HOST': 'rfdocs.org', 'SERVER_NAME': 'rfdocs.org'}
    # Lookup the request path:
    if namespace:
        view_name = namespace + ":" + view_name
    try:
        request.path = reverse(view_name, args=args)
    except NoReverseMatch:
        return
    # get cache key, expire if the cached item exists:
    key = get_cache_key(request, key_prefix=key_prefix)
    if key:
        if cache.get(key):
            # Delete the cache entry.
            #
            # Note that there is a possible race condition here, as another
            # process / thread may have refreshed the cache between
            # the call to cache.get() above, and the cache.set(key, None)
            # below.  This may lead to unexpected performance problems under
            # severe load.
            cache.set(key, None, 0)
        return True
    return False


def _clear_cache(backend):
    logging.info('Clearing cache: %s' % backend)
    res = get_cache(backend).clear()
    logging.info('Successfully cleared cache [flush_all]: %s' % backend)
    return res


def clear_dataset_cache():
    return _clear_cache('dataset')
