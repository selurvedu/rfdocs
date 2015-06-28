#!/usr/bin/env python
# -*- coding: utf-8 -*-

#python imports
import os
import subprocess
import logging

#core django imports
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

#third-party apps imports
from rfdocs.mixins.tools import which

#app imports

logger = logging.getLogger(name=__name__)

phantomjs_bin = 'phantomjs'
try:
    phantomjs_bin = settings.PHANTOMJS_BIN
except AttributeError:
    returncode = which(phantomjs_bin, silent=True)
    if returncode:
        raise ImproperlyConfigured("Set the PHANTOMJS_BIN variable in your settings")


class PhantomJSHelper(object):
    def __init__(self, url=None, error_callback=None, script_js=None):
        self.jsfetcher = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fetcher.js' or script_js)
        self.url = url
        self.error_callback = error_callback
        logger.info('Fetching resource from: %s' % self.url)

    def _execute_script(self):
        if self.jsfetcher is None or not os.path.exists(self.jsfetcher):
            return self.error_callback('error', 'IOError. No such file or directory: %s' % self.jsfetcher)
        command = "%s --ignore-ssl-errors=true %s %s" % (phantomjs_bin, self.jsfetcher, self.url)
        logger.debug('Using command: %s' % command)
        phantom_output = ''
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        try:
            stdoutdata, stderrdata = process.communicate()
            # output will be weird, decode to utf-8 to save heartache
            for line in stdoutdata.splitlines():
                phantom_output += '%s\n' % line  # .decode('utf-8')
        except Exception as err:
            process.kill()
            return self.error_callback('error', err)
        if stderrdata:
            return self.error_callback('error', stderrdata)
        return phantom_output

    def get_content(self):
        return self._execute_script()