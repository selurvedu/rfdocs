#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

from rfdocs.utils.parsers.base import RobotFrameworkLibraryParserBase


class RobotFrameworkLibraryParser2_5(RobotFrameworkLibraryParserBase):
    name = _('Robot Framework 2.5')

    def __init__(self, rflib, **kwargs):
        super(self.__class__, self).__init__(rflib, **kwargs)
        self.run_parser(allow_content_modification=False)


class RobotFrameworkLibraryParser2_6(RobotFrameworkLibraryParserBase):
    name = _('Robot Framework 2.6')

    def __init__(self, rflib, **kwargs):
        super(self.__class__, self).__init__(rflib, **kwargs)
        self.run_parser(allow_content_modification=False)


class RobotFrameworkLibraryParser2_7(RobotFrameworkLibraryParserBase):
    name = _('Robot Framework 2.7')

    def __init__(self, rflib, **kwargs):
        super(self.__class__, self).__init__(rflib, **kwargs)
        self.keywords_table_locator = \
            "//h2[text()='Keywords']/following-sibling::table[contains(@class, 'keywords')]/tbody"
        self.run_parser(allow_content_modification=True)


class RobotFrameworkLibraryParser2_8(RobotFrameworkLibraryParserBase):
    name = _('Robot Framework 2.8')

    def __init__(self, rflib, **kwargs):
        super(self.__class__, self).__init__(rflib, **kwargs)
        self.keywords_table_locator = \
            "//h2[text()='Keywords']/following-sibling::table[contains(@class, 'keywords')]/tbody"
        self.run_parser(allow_content_modification=True)
