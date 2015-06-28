#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rfdocs.mixins.memcached_helper import clear_dataset_cache


class Command(BaseCommand):
    """
    A simple management command which clears the site-wide cache.
    """
    help = 'Clear dataset cache.'

    def handle(self, *args, **kwargs):
        try:
            assert settings.CACHES
            clear_dataset_cache()
            self.stdout.write('Your cache[dataset] has been cleared!\n')
        except AttributeError:
            raise CommandError('You have no cache configured!\n')