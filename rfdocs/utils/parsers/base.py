#!/usr/bin/env python
# -*- coding: utf-8 -*-
import StringIO
import logging
logger = logging.getLogger(name=__name__)
import re
import urllib

from abc import ABCMeta, abstractproperty
from collections import deque
from lxml import html as lh
from lxml.html.clean import Cleaner

from rfdocs.exceptions import RobotFrameworkLibraryDocParseFailedError
from rfdocs.templatetags.rfdocs_tags import generate_node_key


class RobotFrameworkLibraryParserAbstract(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def keywords(self):
        raise NotImplementedError('Must be implemented in subclass')

    @abstractproperty
    def content(self):
        raise NotImplementedError('Must be implemented in subclass')

    @abstractproperty
    def meta_info(self):
        raise NotImplementedError('Must be implemented in subclass')


class RobotFrameworkLibraryParserBase(RobotFrameworkLibraryParserAbstract):
    def __init__(self, rflib_obj, **kwargs):
        self.rflib_obj = rflib_obj
        f = StringIO.StringIO(rflib_obj.original_doc)
        try:
            self.doc = lh.parse(f)
        except Exception:
            raise
        finally:
            f.close()
        self.footer_locator = "//p[@id='footer' or @class='footer']"
        self.keywords_table_locator = \
            "//h2[text()='Keywords']/following-sibling::table[contains(@class, 'keywords')]"
        self.shortcuts_table_locator = "//div[@class='shortcuts']"
        self.strict_mode = True
        self.parser_modified_content = False
        self.modified_doc = None
        self.clean_js = kwargs.get('clean_javascript', False)
        self.clean_elements = kwargs.get('clean_elements', ())
        logger.info('Parsing library: %s' % self.rflib_obj)
        logger.debug('Parsing library %s. Clean scripts: %s. Clean elements: %s' %
                     (self.rflib_obj, self.clean_js, ', '.join(self.clean_elements)))

    def remove_elements(self):
        if not any(self.clean_elements):
            logger.debug('No elements to remove')
            self.parser_modified_content = False
            return
        for item in self.clean_elements:
            logger.debug('Removing elements by locator: %s' % item)
            elems = self.doc.xpath(item)
            logger.debug('Resolved locator for: %s' % item)
            if elems:
                for elem in elems:
                    if elem is not None:
                        logger.debug('Removing element: %s' % elem)
                        elem.getparent().remove(elem)
        self.modified_doc = self.doc
        self.parser_modified_content = True

    def remove_scripts(self):
        if not self.clean_js:
            logger.debug('Scripts will not be removed')
            self.parser_modified_content = False
            return
        cleaner = Cleaner()
        # don't modify original page structure, eg, <head>, <html>, <body> ...
        cleaner.page_structure = False
        # don't remove inline javascript
        cleaner.javascript = False
        # remove <script> tags
        cleaner.scripts = True
        self.modified_doc = cleaner.clean_html(self.doc)
        self.parser_modified_content = True
        logger.debug('Scripts were successfully removed')

    def get_footer(self, locator=None):
        result = self.doc.xpath(locator or self.footer_locator)
        logger.debug('Resolved footer locator: %s' % result)
        if not result:
            raise RobotFrameworkLibraryDocParseFailedError('Failed to get \'Footer\' section')
        self.footer = result[0].text_content()

    def get_shortcuts_table(self, locator=None):
        result = self.doc.xpath(locator or self.shortcuts_table_locator)
        logger.debug('Resolved shortcuts table locator: %s' % result)
        if not result:
            raise RobotFrameworkLibraryDocParseFailedError('Failed to get \'Shortcuts\' section.')
        self.shortcuts_table = result[0]

    def get_keywords_table(self, locator=None):
        result = self.doc.xpath(locator or self.keywords_table_locator)
        logger.debug('Resolved keywords table locator: %s' % result)
        if not result:
            raise RobotFrameworkLibraryDocParseFailedError('Failed to get \'Keywords\' table.')
        self.keywords_table = result[0]

    def rewrite_urls(self):
        # allows to find(focus on and activate) element in the tree
        # and use it for history management
        logger.debug('Rewriting URLs')
        abs_url = self.rflib_obj.get_absolute_url()
        shortcuts_list = [
            a_tag.text.replace(u'\xa0', u' ') for a_tag in self.shortcuts_table.iterchildren()
        ]

        for a_tag in self.keywords_table.iterdescendants('a'):
            href_attr = a_tag.get('href')
            if href_attr and href_attr.startswith('#'):

                href_attr = href_attr.strip('#')
                href_attr = urllib.unquote(href_attr)
                # this means that we have this item in tree also???
                if href_attr in shortcuts_list:
                    # set 'full' relative path for keyword, like version/library/keyword/
                    # each URL must end with slash '/' character
                    a_tag.set('href', '%s%s/' % (abs_url, href_attr,))
                    node_key = generate_node_key(self.rflib_obj.library.name,
                                                 self.rflib_obj.name, href_attr)
                    a_tag.set('data-nodekey', node_key)
                # we are reading the library doc and navigating
                # inside single doc, not a separate keyword?
                else:
                    a_tag.set('href', '%s#%s' % (self.rflib_obj.source_url, href_attr,))
                    node_key = generate_node_key(self.rflib_obj.library.name,
                                                 self.rflib_obj.name)
                    a_tag.set('data-nodekey', node_key)

    def run_parser(self, allow_content_modification=True):
        logger.debug('Running parser')
        self.get_shortcuts_table()
        self.get_keywords_table()
        self.get_footer()
        self.rewrite_urls()
        if allow_content_modification:
            logger.debug('Modifying content')
            self.remove_elements()
            self.remove_scripts()
        return self.parser_modified_content

    @property
    def content(self):
        if self.parser_modified_content:
            return lh.tostring(self.modified_doc)
        return None

    @property
    def meta_info(self):
        logger.debug('Getting meta information from footer')
        mo = re.match(r'.*Altogether (?P<num>\d+) keywords.*Generated.*on(?P<gen_date>.*)\.',
                      self.footer,
                      re.M | re.DOTALL)
        if mo:
            num = int(mo.group('num'))
            gen_date = mo.group('gen_date').strip()
            logger.debug('Parsed footer. Number of keywords: %s. '
                         'Generated on: %s' % (num, gen_date))
        else:
            raise RobotFrameworkLibraryDocParseFailedError('Failed to parse footer')
        return {'kws_num': num, 'gen_date': gen_date}

    @property
    def keywords(self):
        logger.debug('Iterating keywords')
        rows_iterator = self.keywords_table.iterchildren('tr')
        next(rows_iterator)  # skip 'th' instead of checking each time with 'if' statement
        for tr in rows_iterator:
            td_name, td_arg, td_doc = deque(tr.iterchildren('td'), maxlen=3)
            name = td_name.find('a').get('name').replace('%20', u' ')
            arg = td_arg.text
            doc = (td_doc.text or '') + ''.join(
                [lh.tostring(child) for child in td_doc.iterchildren()]
            )
            yield name, arg, doc
