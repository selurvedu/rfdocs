#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from dateutil.parser import parse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from model_utils import Choices
from model_utils import FieldTracker
from model_utils.fields import StatusField, AutoCreatedField, AutoLastModifiedField
from model_utils.managers import PassThroughManager

from rfdocs.exceptions import RobotFrameworkLibraryDocParseFailedError
from rfdocs.fields import ContentTypeRestrictedURLField, AutoSlugField
from rfdocs.mixins import memcached_helper
from rfdocs.utils.downloaders.downloader import DownloadExternalResource
from rfdocs.utils.parsers.parser import RobotFrameworkLibraryParser


ALLOWED_CONTENT_TYPES = settings.RFDOCS.get('ALLOWED_CONTENT_TYPES')
MAX_FILE_SIZE = settings.RFDOCS.get('MAX_FILE_SIZE')
FORCE_HTTP_IN_JSON_DATA = settings.RFDOCS.get('FORCE_HTTP_IN_JSON_DATA')

logger = logging.getLogger(name=__name__)


class RFLibrary(models.Model):
    name = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
    )

    codename = models.CharField(
        max_length=64,
        unique=False,
        blank=True,
        null=True,
        help_text=_('Optionally define a codename.'),
    )

    slug = AutoSlugField(
        _('slug'),
        from_field='name',
        allow_dots=True,
        max_length=64,
        help_text=_('Automatically built from the \'name\' field. '
                    'A slug is a short label generally used in URLs.'),
    )

    tracker = FieldTracker(fields=['name', 'slug', ])

    class Meta:
        ordering = ('name',)
        verbose_name = _('Library')
        verbose_name_plural = 'Libraries'

    def __unicode__(self):
        return '%s [%s]' % (self.name, self.codename) if self.codename else self.name

    def __str__(self):
        return '%s <%s>' % (self.name, self.codename) if self.codename else self.name

    def save(self, **kwargs):
        if self.id:
            if any([self.tracker.has_changed('name'), self.tracker.has_changed('slug')]):
                self.invalidate_cache()
                for version in self.versions.all():
                    version.save(library_renamed=True)

        super(RFLibrary, self).save(**kwargs)
        logger.info('Saved library: %s' % self.__unicode__())

    def delete(self, using=None):
        self.invalidate_cache()
        memcached_helper.clear_dataset_cache()
        super(RFLibrary, self).delete(using=using)
        logger.info('Deleted library: %s' % self.__unicode__())

    def get_absolute_url(self):
        return reverse('rflibrary_detail', args=[self.slug])

    def get_relative_url(self):
        return reverse_lazy('rflibrary_detail', urlconf='rfdocs.urls.libraries',
                            args=[self.slug])

    def get_api_url(self):
        return reverse('rflibrary_detail_api', args=[self.slug])

    def invalidate_cache(self):
        return memcached_helper.expire_view_cache('rflibrary_detail',
                                                  args=[self.slug])

    def invalidate_versions_cache(self):
        return dict([(ver, ver.invalidate_cache()) for ver in self.versions.all()])

    def invalidate_keywords_cache(self):
        return dict([(ver, ver.invalidate_keywords_cache()) for ver in self.versions.all()])


class RFLibraryVersionQueryset(QuerySet):
    def by_author(self, user):
        return self.filter(added_by=user)

    def published(self):
        return self.filter(
            Q(date_deprecate__isnull=True) |
            Q(date_deprecate__gte=timezone.now()),
            date_added__lte=timezone.now(),
            status__exact=RFLibraryVersion.STATUS.published
        )

    def deprecated(self):
        return self.filter(
            Q(date_deprecate__isnull=False) |
            Q(date_deprecate__lte=timezone.now()) |
            Q(status__exact=RFLibraryVersion.STATUS.deprecated),
        )

    def draft(self):
        return self.filter(status__exact=RFLibraryVersion.STATUS.draft)

    def not_draft(self):
        return self.filter(
            ~Q(status__exact=RFLibraryVersion.STATUS.draft),
        )


class RFLibraryVersion(models.Model):
    def __init__(self, *args, **kwargs):
        super(RFLibraryVersion, self).__init__(*args, **kwargs)
        if self.id:
            if self.date_deprecate \
                    and self.date_deprecate <= timezone.now() \
                    and self.status == self.STATUS.published:
                self.status = self.STATUS.deprecated
                self.save(avoid_loop=True)

    name = models.CharField(
        max_length=64,
    )

    library = models.ForeignKey(
        RFLibrary,
        blank=False,
        related_name='versions',
    )

    slug = AutoSlugField(
        _('slug'),
        from_field='name',
        allow_dots=True,
        max_length=64,
        help_text=_('Automatically built from the name. '
                    'A slug is a short label generally used in URLs.'),
    )

    source_url = ContentTypeRestrictedURLField(
        content_types=ALLOWED_CONTENT_TYPES,
        max_upload_size=MAX_FILE_SIZE,
        verbose_name=_('Source URL')
    )

    use_source_url = models.BooleanField(
        default=True,
        verbose_name=_('Use source URL as a location of library documentation')
    )

    original_doc = models.CharField(
        blank=True,
        verbose_name=_('Original HTML document'),
        max_length=MAX_FILE_SIZE
    )

    parsed_doc = models.CharField(
        blank=True,
        verbose_name=_('Parsed HTML document'),
        max_length=MAX_FILE_SIZE
    )

    PARSER = Choices(*RobotFrameworkLibraryParser.get_parsers())
    parser = models.CharField(
        max_length=64,
        choices=PARSER,
        verbose_name=_('Parser'),
        help_text=_('Select parser to be used for parsing the document.'),
    )

    clean_js = models.BooleanField(
        default=True,
        verbose_name=_('Clean JavaScript tags in HTML document.'),
        help_text=_('Use it for documents that were generated with JQuery Templates Plugin.'),
    )

    similar = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name=_('Related Libraries'),
    )

    date_generated = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Document generated on'),
        help_text='The timestamp from HTML document.'
    )

    date_added = AutoCreatedField(
        editable=True,
        db_index=True,
        verbose_name=_('Date added'),
    )

    date_modified = AutoLastModifiedField(
        editable=True,
        db_index=True,
        verbose_name=_('Date modified'),
        help_text=_('The date and time when the library was last saved.'),
    )

    date_deprecate = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Deprecate date'),
        help_text=_('Leave blank if the library should not be marked '
                    'as \'Deprecated\' in the future.'),
    )

    STATUS = Choices(
        ('published', _('Published'),),
        ('draft', _('Draft'),),
        ('deprecated', _('Deprecated'),),
    )

    status = StatusField()

    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        editable=False,
        verbose_name=_('Added by user'),
    )

    tags = models.ManyToManyField(
        'RFTag',
        blank=True,
        related_name='versions',
        help_text=_('Tags.'),
    )

    html_elements = models.ManyToManyField(
        'HtmlElement',
        blank=True,
        related_name='+',
        help_text=_('HTML elements to remove from Library documentation.'),
    )

    tracker = FieldTracker(fields=['source_url', 'original_doc', 'library', 'name', 'parser', ])

    objects = PassThroughManager.for_queryset_class(RFLibraryVersionQueryset)()

    class Meta:
        ordering = ['-date_modified']
        verbose_name_plural = _('Versions')
        verbose_name = _('Version')
        get_latest_by = 'date_added'
        unique_together = (
            ('name', 'library'),
        )
        index_together = [
            ['name', 'library', ],
        ]

    def __unicode__(self):
        return '%s [%s]' % (self.library.name, self.name)

    def __str__(self):
        return '%s <%s>' % (self.library.name, self.name)

    def save(self, **kwargs):
        library_renamed = kwargs.pop('library_renamed', None)
        changed = self.tracker.changed()

        if library_renamed:
            self.invalidate_cache()
            self.invalidate_keywords_cache()
            self.keywords.all().delete()

        if any([changed.get('source_url'), changed.get('library'), changed.get('name')]):
            self.invalidate_cache()
            self.invalidate_keywords_cache()
            self.invalidate_library_cache()
            self.keywords.all().delete()

        super(RFLibraryVersion, self).save(**kwargs)
        logger.info('Saved library: %s' % self)

    def delete(self, using=None):
        self.invalidate_cache()
        self.invalidate_keywords_cache()
        self.invalidate_library_cache()
        super(RFLibraryVersion, self).delete(using=using)
        logger.info('Deleted library: %s' % self)

    def get_absolute_url(self):
        return reverse('rflibraryversion_detail', args=[self.library.slug, self.slug])

    def get_relative_url(self):
        return reverse_lazy('rflibraryversion_detail', urlconf='rfdocs.urls.versions',
                            args=[self.library.slug, self.slug])

    def get_api_url(self):
        return reverse('rflibraryversion_detail_api', args=[self.library.slug, self.slug])

    def get_html_elements(self):
        return [
            i for l in self.html_elements.values_list('locator',
                                                      flat=True) for i in l.split(',')
            ]

    def clean_fields(self, exclude=None):
        if self.original_doc and not self.tracker.has_changed('source_url'):
            exclude = ['source_url', ]
        super(RFLibraryVersion, self).clean_fields(exclude=exclude)

    def clean(self):
        if not any([self.original_doc, self.source_url]):
            raise ValidationError(_("Specify the source of the library."))

    def invalidate_cache(self):
        return memcached_helper.expire_view_cache('rflibraryversion_detail',
                                                  args=[self.library.slug, self.slug, ])

    def invalidate_library_cache(self):
        return self.library.invalidate_cache()

    def invalidate_keywords_cache(self):
        return dict([(kw, kw.invalidate_cache()) for kw in self.keywords.all()])

    @property
    def tags_as_string(self):
        return u', '.join([tag.name for tag in self.tags.all()])

    @property
    def tags_as_list(self):
        return [tag.name for tag in self.tags.all()]

    @property
    def tags_urls_list(self):
        return [tag.get_absolute_url() for tag in self.tags.all()]

    @property
    def keywords_names(self):
        return [kw for kws in self.keywords.all() for kw in kws]

    def fetch_html_document_form_external_url(self):
        fetcher = DownloadExternalResource(url=self.source_url)
        self.keywords.all().delete()
        # Ideally, here we should get response from cache.
        # Otherwise the request will be initiated again.
        data = fetcher.get_response_from_cache_or_raise_error()
        self.original_doc = data
        self.save()

    def parse_library(self, **kwargs):
        print "parse_library::kwargs",kwargs
        if not self.original_doc:
            return 'Nothing to parse.'
        try:
            parser = RobotFrameworkLibraryParser(self.parser, self, **kwargs)
        except (RobotFrameworkLibraryDocParseFailedError, AttributeError) as err:
            logger.exception(err)
            return err
        if parser.content:
            self.parsed_doc = parser.content
        self.date_generated = parse(parser.meta_info.get('gen_date'))
        self.save()
        self.keywords.all().delete()
        kws = []
        for keyword_name, keyword_args, keyword_doc in parser.keywords:
            kw = RFKeyword(name=keyword_name,
                           arguments=keyword_args,
                           documentation=keyword_doc,
                           version=self)
            kws.append(kw)
        self.keywords.add(*kws)


class RFKeyword(models.Model):
    name = models.CharField(
        max_length=256,
    )

    version = models.ForeignKey(
        RFLibraryVersion,
        related_name='keywords',
    )

    arguments = models.TextField(
        null=True,
        blank=True,
        help_text=_('Keyword arguments.'),
    )

    documentation = models.TextField(
        null=True,
        blank=True,
        help_text=_('Keyword documentation.'),
    )

    class Meta:
        ordering = ('name',)
        verbose_name = _('Keyword')
        verbose_name_plural = _('Keywords')
        unique_together = (
            ('name', 'version')
        )
        index_together = [
            ['name', 'version']
        ]

    def __unicode__(self):
        return '%s.%s.%s' % (self.version.library, self.version.name, self.name)

    def __str__(self):
        return '%s [%s.%s]' % (self.name, self.version.library, self.version.name)

    def delete(self, using=None):
        self.invalidate_cache()
        super(RFKeyword, self).delete(using=using)

    def get_absolute_url(self):
        return reverse('rfkeyword_detail',
                       args=[self.version.library.slug, self.version.slug, self.name])

    def get_relative_url(self):
        return reverse_lazy(
            'rfkeyword_detail',
            urlconf='rfdocs.urls.keywords',
            args=[self.library.version.slug, self.library.slug, self.name, ]
        )

    def get_api_url(self):
        return reverse('rfkeyword_detail_api',
                       args=[self.version.library.slug, self.version.slug, self.name])

    @property
    def library_version_keyword(self):
        return '%s.%s.%s' % (self.version.library.name, self.version.name, self.name)

    @property
    def version_library_keyword(self):
        return '%s.%s.%s' % (self.version.name, self.version.library.name, self.name)

    @property
    def library_keyword(self):
        return '%s.%s' % (self.version.library.name, self.name)

    def get_signature(self):
        if self.arguments:
            args = self.arguments.split(',')
            if len(args) == 1:
                return '  %s\n' % args[0]
            args = '\n'.join(['... %s' % arg.strip() for arg in args])
            return '\n%s\n' % args
        return '\n'

    def get_signature_formatted(self):
        if self.arguments:
            args = self.arguments.split(',')
            if len(args) == 1:
                return '%s  %s\n' % (self.name, args[0])
            args = '\n'.join(['... %s' % arg.strip() for arg in args])
            return '%s\n%s\n' % (self.name, args,)
        return '%s\n' % self.name

    def invalidate_cache(self):
        return memcached_helper.expire_view_cache('rf_keyword_detail',
                                                  args=[self.version.library.slug,
                                                        self.version.slug, self.name, ])


class RFTag(models.Model):
    name = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
    )

    slug = models.SlugField(
        _('slug'),
        help_text=_('Automatically built from the name. '
                    'A slug is a short label generally used in URLs.'),
    )

    class Meta:
        ordering = ['-name']
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('rftag_detail', args=[self.slug])

    def get_api_url(self):
        return reverse('rftag_detail_api', args=[self.slug])


class HtmlElement(models.Model):
    name = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        db_index=False,
    )

    locator = models.TextField(
        verbose_name=_('Element to remove from HTML document'),
        help_text=_('Use xpath syntax.'),
        blank=True
    )

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name
