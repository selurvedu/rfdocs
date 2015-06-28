#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from lxml import html as lh
from lxml import etree
from cStringIO import StringIO

from django import template
from django.conf import settings
from django.core.urlresolvers import resolve
from django.template import TemplateSyntaxError, Node, Template
from django.template.defaulttags import include_is_allowed
from django.utils.text import slugify


register = template.Library()
logger = logging.getLogger(name=__name__)

PROJ_TITLE = settings.RFDOCS.get('PROJ_TITLE')


def _generate_ui_element(separator, *args):
    try:
        return separator.join(args)
    except TypeError as err:
        logger.warn("Wrong arguments passed: '%s'. Forcing coerce to string." % err)
        return separator.join([str(arg) for arg in args])


@register.simple_tag
def generate_page_title(*args):
    """
    Generates page title based on arguments.

    Args:
        *args: Strings to be used for constructing title of the page.

    Returns:
        str: Page title concatenated with main project's title.
        An example of returned value:
        Robot Framework 2.6 :: SeleniumLibrary :: Add Location Strategy
    """
    args = (PROJ_TITLE,) + args
    return _generate_ui_element(' :: ', *args)


@register.simple_tag
def generate_node_key(*args):
    """
    Generates node keys needed for history handling and actions on tree nodes.

    Args:
        *args: Strings to be used for construction of unique ID of the element.

    Returns:
        str: Page title concatenated with main project's title.
        It is used either in element's `data` attribute or as a data-* attribute.
        An example of returned value:
        robot-27_seleniumlibrary_assign-id-to-element
    """
    return slugify(_generate_ui_element('_', *args))


@register.assignment_tag
def get_settings_param(param):
    return getattr(settings, param, False)


@register.simple_tag
def dynamic_content():
    """
    Silly tag to put proper class.
    """
    return ' dynamic-content'


@register.filter
def status_indicator(status):
    """
    Associates status of RFLibrary class to Bootstrap CSS class.

    Args:
        status (str): Status of the :model:`rfdocs.RFLibrary`.

    Returns:
        str: Relevant CSS class.
    """
    status_map = {
        'published': 'success',
        'draft': 'important',
        'deprecated': 'warning'
    }
    return status_map.get(status)


@register.filter
def get_range(value):
    """
    Filter - returns a list containing range made from given value.

    Args:
        value (int): A value to build range from.

    Returns:
        list: The range of values.

    Examples:
        <ul>{% for i in 3|get_range %}
          <li>{{ i }}. Do something</li>
        {% endfor %}</ul>
        Results with the HTML:
        <ul>
          <li>0. Do something</li>
          <li>1. Do something</li>
          <li>2. Do something</li>
        </ul>
    """
    return range(int(value))


@register.simple_tag(takes_context=True)
def active(context, url_name, return_value='active', **kwargs):
    matches = current_url_equals(context, url_name, **kwargs)
    return return_value if matches else ''


def current_url_equals(context, url_name, **kwargs):
    resolved = False
    try:
        resolved = resolve(context.get('request').path)
    except Exception:
        pass
    matches = resolved and resolved.url_name == url_name
    if matches and kwargs:
        for key in kwargs:
            kwarg = kwargs.get(key)
            resolved_kwarg = resolved.kwargs.get(key)
            if not resolved_kwarg or kwarg != resolved_kwarg:
                return False
    return matches


@register.inclusion_tag('rfdocs/common/filter_tags.html')
def get_filter_tags(obj):
    return {'filter_tags': obj.tags.all()}


@register.filter
def pdb(element):
    import pdb
    pdb.set_trace()
    return element


class SsiNodeGetByLocator(Node):
    """
    This class is modification of `SsiNode` class from Django's defaulttags.py module.

    Uses `lxml` module to parse HTML document ang get content defined by locator.

    Attributes:
        locator (str):  The xpath locator.
        filepath (str): The path to file to read data from.
        parsed (str): Optional parameter that makes the contents of
        the included file to be evaluated as template code,
        within the current context:
    """
    def __init__(self, locator, filepath, parsed):
        self.locator = str(locator)
        self.filepath = filepath
        self.parsed = parsed

    def render(self, context):
        filepath = self.filepath.resolve(context)
        if not include_is_allowed(filepath):
            if settings.DEBUG:
                return "[Didn't have permission to include file]"
            else:
                return ''  # Fail silently for invalid includes.
        try:
            with open(filepath, 'r') as fp:
                tree = etree.parse(StringIO(fp.read()), etree.HTMLParser())
            output = ''
            for child in tree.find(self.locator).iterchildren():
                output += lh.tostring(child)
        except IOError:
            output = ''
        if self.parsed:
            try:
                t = Template(output, name=filepath)
                return t.render(context)
            except TemplateSyntaxError as e:
                if settings.DEBUG:
                    return "[Included template had syntax error: %s]" % e
                else:
                    return ''  # Fail silently for invalid included templates.
        return output

@register.tag
def ssi_get_part(parser, token):
    """
    Outputs the contents of a given file into the page.

    This is modification of `ssi` built-in tag.
    """
    bits = token.split_contents()
    parsed = False
    if len(bits) not in (3, 4):
        raise TemplateSyntaxError("'ssi_get_part' tag takes two arguments: locator to get content "
                                  "from and the path to the file to be included")
    if len(bits) == 4:
        if bits[3] == 'parsed':
            parsed = True
        else:
            raise TemplateSyntaxError("Third (optional) argument "
                                      "to %s tag must be 'parsed'" % bits[0])
    locator = parser.compile_filter(bits[1])
    filepath = parser.compile_filter(bits[2])
    return SsiNodeGetByLocator(locator, filepath, parsed)
