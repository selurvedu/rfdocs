#!/usr/bin/env python
# -*- coding: utf-8 -*-

#python imports
import logging
import re
import requests
import requests_cache
from requests_cache import CachedSession

#core django imports
from django.core import exceptions
from django.conf import settings
#third-party apps imports

#app imports
from .alternate.phantomjs import PhantomJSHelper

logger = logging.getLogger(name=__name__)

requests_cache.install_cache(cache_name="downloader_cache", expire_after=90)


class DownloadExternalResource(object):
    def __init__(self,
                 url=None,
                 max_file_size=None,
                 allowed_content_types=(),
                 jsfetcher=None,
                 marker=r'<meta.*name="Generator".*>'):
        logger.info('Running downloader for url: %s' % url)
        self.url = str(url)
        self.max_file_size = max_file_size or settings.RFDOCS.get('MAX_FILE_SIZE')
        self.allowed_content_types = allowed_content_types or settings.RFDOCS.get('ALLOWED_CONTENT_TYPES')

        self.s = CachedSession()
        self.r = None
        self.error = {}
        self.jsfetcher = jsfetcher
        self.marker = marker

    def _set_error(self, key, value):
        self.error[key] = value
        return self.error

    def _no_error(self):
        self.error = {}
        return self.error

    def send_request(self):
        logger.info('Download external resource: %s' % self.url)
        try:
            self.r = self.s.get(self.url)
        except (requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema,
                requests.exceptions.ConnectionError,) as error:
            logger.warn("Failed to download resource. Error: %s" % error)
            self._set_error('error', error)

    def get_response(self):
        # Workaround for Robot Framework libraries with version >= 2.8 (or even 2.7).
        # Libraries are generated with JQuery templates system.
        # Python's `requests` module fetches raw content, of course not rendered HTML.
        # Thus parser will fail in such cases.
        # For this reason an awesome PhantomJS is used. Unfortunately `requests_cache` module
        # wont help here because PhantomJS has to request the URL by its
        # own methods to be able to render HTML.
        # One more notice is that I don't use PhantomJS native features to actually write data to filesystem.
        # (PhantomJS has `fs` module to work with filesystem).
        # Why? I don't know yet :)

        # Instead use `subprocess.Popen` to execute javascript code,
        # let PhantomJS to do his job and give the output back to python.

        # Anyway I want the resource to be validated by Django's validators before we can proceed.
        # So if we came here, the validation has passed.

        # First, check if response content has
        # meta tag with name="Generator"
        # If so, the document uses JQuery templates plugin system and we need help of PhantomJS.
        content = self.r.content
        mo = re.search(self.marker, content, re.DOTALL | re.M | re.I)
        if not mo:
            return content
        logger.info('Using phantomjs to download resource')
        alternate_downloader = PhantomJSHelper(url=self.url, error_callback=self._set_error)
        return alternate_downloader.get_content()

    def validate_response(self):
        logger.info('Validate external resource: %s' % self.url)
        if not self.r:
            self.send_request()
        if self.error:
            return self.error
        try:
            self.r.raise_for_status()
        except requests.exceptions.HTTPError as error:
            logger.warn("Failed to fetch resource. Error: %s" % error)
            return self._set_error('error', error)
        if self.r.status_code == requests.codes.ok:
            content_len = self.r.headers.get('content-length', None)
            if content_len:
                csize = int(content_len)
            else:
                csize = len(self.r.content)
            if csize < self.max_file_size:
                ctype_header = self.r.headers.get('content-type')
                if not ctype_header:
                    return self._set_error('content_type',
                                           'Response does not contain the \'Content-Type\' header. Rejected.')
                ctype = ctype_header.split(';')[0].lower()
                if ctype in [ct.lower() for ct in self.allowed_content_types]:
                    # the place where all the procedure passed and we succeeded
                    return self._no_error()
                else:
                    logger.warn("Failed to fetch resource. "
                                "Allowed content types are: %s."
                                "The content type is: %s" % (', '.join(self.allowed_content_types), ctype,))
                    return self._set_error('content_type', ctype)

            else:
                logger.warn("Failed to fetch resource. "
                            "The content size \'%s\' exceeds maximum allowed size: %s" % (self.max_file_size, csize))
                return self._set_error('content_size', csize)
        else:
            error = requests.exceptions.HTTPError(self.r.status_code)
            logger.warn("Failed to fetch resource. Error: %s" % error)
            return self._set_error('error', error)

    def get_response_from_cache(self):
        if not self.s.cache.has_url(self.url):
            self.send_request()
            self.validate_response()
            return self.get_response()
        self.r = self.s.get(self.url)
        return self.get_response()

    def get_response_from_cache_or_raise_error(self):
        response = self.get_response_from_cache()
        if self.error:
            err = self.error.get('error')
            # these are model's `clean` ValidationError (not the same as forms.ValidationError)
            if err:
                raise exceptions.ValidationError(err)
            else:
                raise exceptions.ValidationError(self.error)
        return response
