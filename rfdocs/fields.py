#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db import models
from django.forms import forms
from django.template.defaultfilters import filesizeformat, slugify
from django.utils.translation import ugettext_lazy as _

from rfdocs.filters import slugify_allow_dots
from rfdocs.utils.downloaders.downloader import DownloadExternalResource


class ContentTypeRestrictedURLField(models.URLField):
    """
    Customized models.URLField class that extra options.

    Allows to specify:
        * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload.
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """
    def __init__(self, content_types=None, max_upload_size=None, **kwargs):
        """
        Adds option to restrict URLField to certain content types and size.

        Kwargs:
            content_types (list, tuple): Allowed content types like 'text/html', 'text/plain' etc.
            max_upload_size (int): Maximum allowed file size in bytes.
            kwargs (dict): Other parameters for models.URLField class.
        """
        self.content_types = content_types
        self.max_upload_size = max_upload_size
        super(ContentTypeRestrictedURLField, self).__init__(**kwargs)

    def clean(self, *args, **kwargs):
        """
        Performs 'clean' on models.URLField field.

        Also fetches the data from the URL and verifies it's content-type
        and size values.
        This method will re-fetch the data every time current method is called!

        Returns:
            str. If URLField validation is passed, it returns URL.

        Raises:
            forms.ValidationError
        """
        # if URLField validation has passed, it should return URL
        url = super(ContentTypeRestrictedURLField, self).clean(*args, **kwargs)
        fetcher = DownloadExternalResource(url=url,
                                           max_file_size=self.max_upload_size,
                                           allowed_content_types=self.content_types)
        fetcher.send_request()
        error = fetcher.validate_response()
        if error:
            # first check if we have any exceptions raised
            ex = error.get('error')
            if ex:
                raise forms.ValidationError(ex)
            # now check if the file that is being fetched
            # has correct content-type and size
            csize = error.get('content_size')
            if csize:
                raise forms.ValidationError(_('Please keep filesize under %s. Current filesize %s') %
                                            (filesizeformat(self.max_upload_size), filesizeformat(csize)))
            ctype = error.get('content_type')
            if ctype:
                raise forms.ValidationError(_('Filetype "%s" not supported. Must be one of the following: %s' %
                                              (ctype, ', '.join(self.content_types)),))
        return url


class AutoSlugField(models.SlugField):
    __metaclass__ = models.SubfieldBase
    description = _('slugify that allows to use dot(.) in a slug field.')

    def __init__(self, *args, **kwargs):
        self._from_field = kwargs.pop('from_field', None)
        self._allow_dots = kwargs.pop('allow_dots', False)
        super(AutoSlugField, self).__init__(*args, **kwargs)

    def pre_save(self, instance, add):
        attr = self._from_field or self.attname
        potential_slug = getattr(instance, attr)
        if self._allow_dots:
            potential_slug = slugify_allow_dots(potential_slug)
        else:
            potential_slug = slugify(potential_slug)
        setattr(instance, self.attname, potential_slug)
        return potential_slug
