#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(name=__name__)

from copy import copy

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from rfdocs.models import (RFLibrary, RFKeyword, RFLibraryVersion, RFTag, HtmlElement)
from rfdocs.mixins.memcached_helper import clear_dataset_cache
from rfdocs.utils.admin.cache_utils import (invalidate_view_cache, invalidate_children_view_cache,
                                            invalidate_dataset_cache, invalidate_entity_cache,
                                            invalidate_versions_cache, invalidate_keywords_cache)
from rfdocs.utils.admin.filters import CountVersionsListFilter, CountKeywordsListFilter
from rfdocs.utils.admin.model_admin import ButtonModelAdmin


class CustomModelChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        tags_count = obj.tags.count()
        if tags_count:
            return '{} ({})'.format(unicode(obj), tags_count)
        return unicode(obj)


class RFLibraryAdmin(ButtonModelAdmin):

    def get_related_versions(obj):
        values = []
        for v in obj.versions.values_list('name', 'pk'):
            res = reverse('admin:rfdocs_rflibraryversion_change', args=(v[1], ))
            values.append((v[0], res))
        related_versions = ['<a href="%s">%s</a>' % (v[1], v[0]) for v in values]
        return mark_safe(u', '.join(related_versions))

    fieldsets = (
        (None, {
            'fields': (),
            'classes': ('wide', 'alert-danger', 'hide'),
            'description': 'Some description '
        }),
        (None, {
            'fields': ('name', 'slug', 'codename',),
            'classes': ('wide',),
            'description': 'Please be extremely careful when setting fields in this section.'
        }),
    )

    get_related_versions.allow_tags = True
    get_related_versions.short_description = 'Versions'

    list_display = ('name', 'codename', get_related_versions,)
    list_filter = ('name', 'codename', CountVersionsListFilter)
    readonly_fields = ('slug',)

    class Media:
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'admin/js/handle_change_form_common.js',
        )
        css = {'all': ('admin/css/handle_change_form_common.css', )}

    invalidate_dataset_cache = invalidate_dataset_cache
    invalidate_entity_cache = invalidate_entity_cache
    invalidate_versions_cache = invalidate_versions_cache
    invalidate_keywords_cache = invalidate_keywords_cache

    actions = [invalidate_entity_cache, invalidate_versions_cache, invalidate_keywords_cache,
               invalidate_dataset_cache]
    list_buttons = copy(actions)
    change_buttons = copy(actions)


class RFLibraryVersionAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RFLibraryVersionAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            all_kws = self.instance.keywords.values_list('name', flat=True)
            self.fields['list_of_keywords'] = \
                forms.ModelMultipleChoiceField(queryset=all_kws,
                                               widget=forms.SelectMultiple(),
                                               required=False,
                                               initial=all_kws,
                                               label='Keywords',
                                               help_text=_('Keywords bound to this library.'), )
            self.fields['list_of_keywords'].widget.attrs['disabled'] = 'disabled'
            self.fields['list_of_keywords'].widget.attrs['size'] = len(all_kws) / 2
            self.fields['similar'].queryset = RFLibraryVersion.objects.filter(
                ~Q(id__exact=self.instance.id)
            )
            self.fields['original_doc'].widget.attrs['disabled'] = 'disabled'

    list_of_keywords = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=FilteredSelectMultiple(verbose_name='Keywords', is_stacked=False),
        initial=(None,)
    )

    tags = forms.ModelMultipleChoiceField(
        queryset=RFTag.objects.all(),
        widget=FilteredSelectMultiple(verbose_name='Tags', is_stacked=False),
        required=False,
        help_text=_('Hold Ctrl(Cmd on OSX) to select separate items '
                    'or Shift for multiple selection.'),
    )

    html_elements = forms.ModelMultipleChoiceField(
        queryset=HtmlElement.objects.all(),
        widget=FilteredSelectMultiple(verbose_name='HTML Elements', is_stacked=False),
        required=False,
        help_text=_('Hold Ctrl(Cmd on OSX) to select separate items '
                    'or Shift for multiple selection.'),
    )

    similar = forms.ModelMultipleChoiceField(
        queryset=RFLibraryVersion.objects.all(),
        widget=FilteredSelectMultiple(verbose_name='Related libraries', is_stacked=False),
        required=False,
        help_text=_('Hold Ctrl(Cmd on OSX) to select separate items '
                    'or Shift for multiple selection.'),
    )

    original_doc = forms.CharField(widget=forms.Textarea, required=False)

    def clean_codename(self):
        return self.cleaned_data['codename'] or None

    class Meta:
        model = RFLibraryVersion
        fields = '__all__'


class RFLibraryVersionAdmin(ButtonModelAdmin):
    def get_number_of_keywords(obj):
        return obj.keywords.count() if obj.keywords else 0
    get_number_of_keywords.short_description = 'Keywords'

    def get_tags_names(obj):
        names = ['<a href="{}">{}</a>'.format(reverse('admin:rfdocs_rftag_change', args=(tag.pk,)),
                                              tag.name) for tag in obj.tags.all()]
        return mark_safe(u', '.join(names))
    get_tags_names.allow_tags = True
    get_tags_names.short_description = 'Tags'

    def get_library(obj):
        version = u'<a href="{}">{}</a>'.format(reverse('admin:rfdocs_rflibrary_change',
                                                        args=(obj.library.pk,)),
                                                obj.library.name)
        return mark_safe(version)
    get_library.allow_tags = True
    get_library.short_description = 'Library'

    list_display = (
        'name',
        get_library,
        'status',
        get_number_of_keywords,
        get_tags_names,
        'added_by',
    )
    list_filter = ('library', 'status', 'tags', CountKeywordsListFilter)
    search_fields = ('name', 'library__name', 'keywords__name')
    # allows to set status without going into library's page
    list_editable = ('status',)
    # Sort and gather fields into sets
    fieldsets = (
        (None, {
            'fields': (),
            'classes': ('wide', 'alert-danger', 'hide'),
            'description': 'Please keep in mind that you if changed anything in the form, you '
                           '<strong>must</strong> save the form </br>'
                           '(press "Save and continue editing" button) before using any of '
                           'form actions on the top of this page. </br>'
                           'The order of actions is:'
                           '<ol>'
                           '<li>Fetch library</li>'
                           '<li>Parse library</li>'
                           '</ol>'
        }),
        (None, {
            'fields': ('name', 'library', 'slug',),
            'classes': ('wide',),
            'description': 'Please be extremely careful when setting fields in this section.'
        }),
        ('Parsing options', {
            'fields': ('parser', 'clean_js', 'html_elements',),
            'classes': ('wide',),
            'description': 'These options are used when \'Parse Library\' button is pressed.'
        }),
        ('Source', {
            'fields': ('source_url', 'use_source_url', 'original_doc'),
            'classes': ('wide',),
            'description': 'The data will be written to local filesystem.'
                           '<br />Please ensure that you use stable source, '
                           'as it may be used for (manual)auto-updates in the future.'
                           '<ul>Limitations:'
                           '<li>Allowed content-types: %s</li>'
                           '<li>Maximum file-size: %s</li>'
                           '</ul>' %
                           (', '.join(settings.RFDOCS.get('ALLOWED_CONTENT_TYPES')),
                            filesizeformat(settings.RFDOCS.get('MAX_FILE_SIZE')))
        }),
        ('Related Libraries', {
            'fields': ('similar',),
            'classes': ('wide',),
            'description': 'Define how current library relates with other libraries.',
        }),
        ('Tags', {
            'fields': ('tags',),
            'classes': ('wide',),
            'description': 'Tags allow quickly filter/find needed items. '
                           'For simplicity, please try to keep minimum set of tags per item.',
        }),
        ('Keywords', {
            'fields': ('list_of_keywords',),
            'classes': ('wide', ),
            'description': 'List of Keywords in the Library.',
        }),
        ('Metadata', {
            'fields': ('date_generated', 'date_added', 'date_modified', 'date_deprecate', 'status'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('slug', 'date_added', 'date_modified', 'date_generated')
    form = RFLibraryVersionAdminForm

    class Media:
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'admin/js/handle_change_form_common.js',
        )
        css = {'all': ('admin/css/handle_change_form_common.css', )}

    def invalidate_cache(self, request, obj=None):
        return invalidate_view_cache(self, request, obj)
    invalidate_cache.short_description = 'Invalidate Version cache'

    def invalidate_library_cache(self, request, obj=None):
        return invalidate_view_cache(self, request, obj.library)
    invalidate_library_cache.short_description = 'Invalidate Library cache'

    def invalidate_keywords_cache(self, request, obj=None):
        return invalidate_children_view_cache(self, request, obj, 'invalidate_keywords_cache')
    invalidate_keywords_cache.short_description = 'Invalidate Keywords cache'

    def invalidate_dataset_cache(self, request, dummy_obj):
        res = clear_dataset_cache()
        self.message_user(request, res, level=messages.INFO)
        return None  # Redirect or Response or None
    invalidate_dataset_cache.short_description = 'Invalidate Dataset cache'

    def fetch_library(self, request, obj=None):
        if obj is not None:
            res = obj.fetch_html_document_form_external_url()
            if res:
                self.message_user(request, res, level=messages.ERROR)
                logger.debug(res)
                return None  # Redirect or Response or None
            self.message_user(request, 'Successfully fetched library.')
            logger.debug('Successfully fetched library')
        return None  # Redirect or Response or None
    fetch_library.short_description = 'Fetch Library'

    def parse_library(self, request, obj=None):
        if obj is not None:
            res = obj.parse_library(clean_javascript=obj.clean_js,
                                    clean_elements=obj.get_html_elements())
            if res:
                self.message_user(request, res, level=messages.ERROR)
                logger.debug(res)
                return None  # Redirect or Response or None
            kws_count = obj.keywords.count()
            if kws_count == 1:
                message_bit = '%s keyword' % (kws_count,)
            else:
                message_bit = '%s keywords' % (kws_count,)
            self.message_user(request, 'Successfully parsed library. Added %s.' % message_bit)
            logger.debug('Successfully parsed library. Added %s.' % message_bit)
        return None  # Redirect or Response or None
    parse_library.short_description = 'Parse Library'

    list_buttons = [fetch_library, parse_library, invalidate_cache, invalidate_library_cache,
                    invalidate_keywords_cache, invalidate_dataset_cache]
    change_buttons = [fetch_library, parse_library, invalidate_cache, invalidate_library_cache,
                      invalidate_keywords_cache, invalidate_dataset_cache]

    def save_model(self, request, obj, form, change):
        """
        Overwrite this method to disable the ability to change author.
        'author' filed now defaults to the username of logged in user.
        """
        if not change:
            obj.added_by = request.user
        obj.save()

    def get_actions(self, request):
        actions = super(RFLibraryVersionAdmin, self).get_actions(request)

        def dynamic_status(name, status):
            def status_func(self, request, queryset):
                rows_updated = queryset.update(status=status)
                if rows_updated == 1:
                    message_bit = '1 library was'
                else:
                    message_bit = '%s libraries were' % rows_updated
                self.message_user(request, '%s successfully changed.' % message_bit)
                logger.debug('%s successfully changed.' % message_bit)

            status_func.__name__ = name
            status_func.short_description = _('Set status of selected to "%s"' % status)
            return status_func

        for status in RFLibraryVersion.STATUS:
            name = 'mark_status_%s' % status[0]
            actions[name] = (dynamic_status(name, status[0]),
                             name,
                             _('Set status of selected to "%s"' % status[0].capitalize()))

        def fetch_library_documentation_from_libraries_list_view(name):
            def worker_func(self, request, queryset):
                counter = 0
                passed = {}
                failed = {}
                for library in queryset.iterator():
                    res = library.fetch_html_document_form_external_url()
                    if res:
                        failed[unicode(library)] = res
                    else:
                        passed[unicode(library)] = 'OK'
                    counter += 1
                if counter == 1:
                    message_bit = lambda num: 'library'
                else:
                    message_bit = lambda num: '%s libraries' % num
                if passed:
                    list_items = _('<ul>%s</ul>') % ' '.join(
                        ['<li>%s - %s</li>' % (k, v) for k, v in passed.iteritems()])
                    final_message = 'Successfully fetched %s. %s' % (
                        message_bit(counter - len(failed.keys())), list_items)
                    self.message_user(request, mark_safe(final_message), level=messages.SUCCESS)
                    logger.debug('Successfully fetched %s' % message_bit)
                if failed:
                    list_items = _('<ul>%s</ul>') % ' '.join(
                        ['<li>%s - %s</li>' % (k, v) for k, v in failed.iteritems()])
                    final_message = 'Failed to fetch %s. %s' % (message_bit(counter - len(passed.keys())), list_items)
                    self.message_user(request, mark_safe(final_message), level=messages.ERROR)
                    logger.debug('Failed to fetch %s' % message_bit)

            worker_func.__name__ = name
            worker_func.short_description = _('Fetch documentation for selected libraries')
            return worker_func

        def parse_library_from_libraries_list_view(name):
            """
            Updates keywords list from libraries list display view.

            Messages for user have HTML embedded. The correct way to do this is via template.
            I don't want to edit the admin template for this purpose only.
            Also the way below may be more reliable when upgrading Django.
            """
            def worker_func(self, request, queryset):
                counter = 0
                passed = {}
                failed = {}
                for library in queryset.iterator():
                    res = library.parse_library(clean_javascript=library.clean_js,
                                                clean_elements=library.get_html_elements())

                    if res:
                        failed[unicode(library)] = res
                    else:
                        passed[unicode(library)] = 'OK'
                    counter += 1
                if counter == 1:
                    message_bit = lambda num: 'library'
                else:
                    message_bit = lambda num: '%s libraries' % num
                if passed:
                    list_items = _('<ul>%s</ul>') % ' '.join(
                        ['<li>%s - %s</li>' % (k, v) for k, v in passed.iteritems()])
                    final_message = 'Successfully parsed %s. %s' % (
                        message_bit(counter - len(failed.keys())), list_items)
                    self.message_user(request, mark_safe(final_message), level=messages.SUCCESS)
                    logger.debug('Successfully parsed %s' % message_bit)
                if failed:
                    list_items = _('<ul>%s</ul>') % ' '.join(
                        ['<li>%s - %s</li>' % (k, v) for k, v in failed.iteritems()])
                    final_message = 'Failed to parse %s. %s' % (message_bit(counter - len(passed.keys())), list_items)
                    self.message_user(request, mark_safe(final_message), level=messages.ERROR)
                    logger.debug('Failed to parse %s' % message_bit)

            worker_func.__name__ = name
            worker_func.short_description = _('Parse selected libraries')
            return worker_func

        actions['Fetch documentation'] = (fetch_library_documentation_from_libraries_list_view('Fetch documentation'),
                                          'Fetch documentation',
                                          _('Fetch documentation for selected libraries'))
        actions['Parse library'] = (parse_library_from_libraries_list_view('Parse library'),
                                    'Parse library',
                                    _('Parse selected libraries'))
        return actions


class RFKeywordAdmin(admin.ModelAdmin):
    list_display = ('name', 'version',)
    list_filter = ('version__name', 'version__library__name',)
    search_fields = ('name', 'version__name', 'version__library__name',)
    readonly_fields = ('name', 'version', 'arguments', 'documentation',)


class RFTagAdminForm(forms.ModelForm):
    versions = CustomModelChoiceField(
        queryset=RFLibraryVersion.objects.all(),
        widget=FilteredSelectMultiple(verbose_name='Libraries', is_stacked=False),
        required=False,
        help_text=_('Select libraries to be tagged with current tags. '
                    'Digit in brackets shows number of tags already assigned.'), )

    class Meta:
        model = RFTag
        fields = '__all__'


class RFTagAdmin(admin.ModelAdmin):
    def get_tagged_libraries(obj):
        return mark_safe(
            u', '.join(
                ['<a href="%s">%s</a>' %
                 (reverse('admin:rfdocs_rflibraryversion_change', args=(l.pk,)), l) for l in obj.versions.all()]
            )
        )

    get_tagged_libraries.allow_tags = True
    get_tagged_libraries.short_description = 'Libraries'

    list_display = ('name', get_tagged_libraries,)
    list_filter = ('name', 'versions__library__name',)
    search_fields = ('name', 'versions__name', 'versions__library__name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'slug'),
            'classes': ('wide',),
        }),
        ('Tagged libraries', {
            'fields': ('versions',),
            'classes': ('wide',)
        }),
    )
    form = RFTagAdminForm
    prepopulated_fields = {'slug': ('name', )}

    class Media:
        js = (
            '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'admin/js/handle_tag_form.js',
        )


class HtmlElementAdmin(admin.ModelAdmin):
    pass


admin.site.register(RFLibrary, RFLibraryAdmin)
admin.site.register(RFLibraryVersion, RFLibraryVersionAdmin)
admin.site.register(RFKeyword, RFKeywordAdmin)
admin.site.register(RFTag, RFTagAdmin)
admin.site.register(HtmlElement, HtmlElementAdmin)
