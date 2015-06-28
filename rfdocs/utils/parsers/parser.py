#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect


from rfdocs.utils.parsers import parsers

__all__ = ['RobotFrameworkLibraryParser',]


class RobotFrameworkLibraryParser(object):
    __dict__ = {}
    __parsers = []

    def __init__(self, cls, rflib_obj, **kwargs):
        parsers_list = [parser[0] for parser in self.__parsers]
        if cls not in parsers_list:
            raise ValueError('Invalid value given: %s. '
                             'Must be one from: %s' % (cls, ', '.join(parsers_list)))
        class_ = getattr(parsers, cls)
        self.instance_ = class_(rflib_obj, **kwargs)

    def __getattr__(self, attr):
        if attr in ('keywords', 'content', 'meta_info'):
            return getattr(self.instance_, attr)

    @classmethod
    def get_parsers(cls):
        classmembers = inspect.getmembers(parsers, inspect.isclass)
        for klass in classmembers:
            # klass[0] - string representation of class
            # klass[1] - class obj
            if klass[1].__dict__.get('name', None):
                cls.__parsers.append((unicode(klass[0]), klass[1].name))
        return tuple(cls.__parsers)
