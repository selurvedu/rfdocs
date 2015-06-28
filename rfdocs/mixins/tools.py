#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess

import warnings
from django.core.exceptions import ImproperlyConfigured


def force_http(url, force=True):
    if not force:
        return url
    return re.sub(r'^https://', 'http://', url)


def get_env_variable(var, fail_to=None):
    """
    Gets the environment variable or returns exception
    """
    res = os.environ.get(var, fail_to)
    if not res:
        raise ImproperlyConfigured("Set the %s environment variable" % var)
    return res


def which(executable, silent=False):
    """
    A very simplified 'which', just for dev needs.
    """
    returncode = subprocess.call(["which", executable])
    if returncode:
        error_message = 'Could not locate \'%s\'. Maybe it is not in system path.' % executable
        if silent:
            warnings.warn(error_message)
        else:
            raise RuntimeWarning(error_message)
    return returncode


class RunUglifyJs(object):
    def __init__(self, project_dir, *args):
        self.target_files = []
        self.options = args
        self.passed = []
        self.failed = []
        self.executable = 'uglifyjs'
        self.project_dir = project_dir
        self.static_js_dev_dir = os.path.join(project_dir, 'rfdocs', 'static', 'js', 'devel')
        self.static_js_min_dir = os.path.join(project_dir, 'rfdocs', 'static', 'js', 'min')

    def add_target_file(self, input_f, output_f):
        f = {
            'in': str(os.path.join(self.static_js_dev_dir, *input_f)),
            'out': str(os.path.join(self.static_js_min_dir, *output_f)),
        }
        self.target_files.append(f)

    def _call_executable(self, *args):
        command = [self.executable]
        command.extend(args)
        print 'Running command: %s' % ' '.join(command)
        return subprocess.call(command)

    def run(self):
        print "Running with executable: %s" % self.executable
        which(self.executable)
        for f in self.target_files:
            f_in = f['in']
            f_out = f['out']
            returncode = self._call_executable(
                f_in, '-c', '-m', '-r', '\'$,Logger,Item,Toolbar,ToolBar,Stack,Dataset,Tree,Filter,UIAPP\'', '-o', f_out
            )
            if not returncode:
                self.passed.append(f_in)
                print "Successfully compressed \'%s\' into \'%s\'" % (f_in, f_out)
            else:
                self.failed.append(f_in)
                print "Failed to compressed \'%s\' into \'%s\'" % (f_in, f_out)
        print "Passed:"
        print "\n".join(self.passed)
        print "Failed:"
        print "\n".join(self.failed)
        print "Result. Total files: %s. Compressed: %s. Failed to compress: %s" % (len(self.target_files),
                                                                                   len(self.passed),
                                                                                   len(self.failed))
