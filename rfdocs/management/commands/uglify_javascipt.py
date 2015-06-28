from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rfdocs.mixins.tools import RunUglifyJs


class Command(BaseCommand):
    """
    A simple management command which clears the site-wide cache.
    """
    help = 'Compress javascript with uglifyjs2.'

    def handle(self, *args, **kwargs):
        try:
            assert settings.BASE_DIR
        except AttributeError:
            raise CommandError('Please define BASE_DIR variable in your settings!\n')
        uglyfier = RunUglifyJs(settings.BASE_DIR)

        uglyfier.add_target_file(('main', 'filter.js'), ('main', 'filter.min.js'))
        uglyfier.add_target_file(('main', 'init.js'), ('main', 'init.min.js'))
        uglyfier.add_target_file(('main', 'item.js'), ('main', 'item.min.js'))
        uglyfier.add_target_file(('main', 'locators.js'), ('main', 'locators.min.js'))
        uglyfier.add_target_file(('main', 'logger.js'), ('main', 'logger.min.js'))
        uglyfier.add_target_file(('main', 'module.js'), ('main', 'module.min.js'))
        uglyfier.add_target_file(('main', 'stack.js'), ('main', 'stack.min.js'))
        uglyfier.add_target_file(('main', 'toolbar.js'), ('main', 'toolbar.min.js'))
        uglyfier.add_target_file(('main', 'tree.js'), ('main', 'tree.min.js'))
        uglyfier.add_target_file(('mixins.js',), ('mixins.min.js',))
        uglyfier.add_target_file(('main.js',), ('main.min.js',))

        uglyfier.add_target_file(('lib', 'jquery.dynatree-1.2.4.js',), ('lib', 'jquery.dynatree-1.2.4.min.js',))

        uglyfier.run()
