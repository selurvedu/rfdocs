#!/usr/bin/env python

# Source: https://github.com/dlrust/python-memcached-stats/blob/master/src/memcached_stats.py

"""
Basic usage:
For my proj
from rfdocs.mixins.memcached_stats import MemcachedStats


from memcached_stats import MemcachedStats
mem = MemcachedStats()

By default, it connects to localhost on port 11211. If you need to specify a host and/or port:

mem = MemcachedStats('1.2.3.4', '11211')

Retrieve a dict containing the current stats from memcached:

mem.stats()
{'accepting_conns': '1',
 'auth_cmds': '0',
 'auth_errors': '0',
 ... }

Retrieve a list of keys currently in use:

mem.keys()
['key-1',
 'key-2',
 'key-3',
 ... ]

List the keys

If you just want to list some of the keys in memcached, run this from the command line:

python -m memcached_stats <ip> <port>
"""

import re
import sys
import telnetlib


class MemcachedStats(object):

    _client = None
    _key_regex = re.compile(ur'ITEM (.*) \[(.*); (.*)\]')
    _slab_regex = re.compile(ur'STAT items:(.*):number')
    _stat_regex = re.compile(ur"STAT (.*) (.*)\r")

    def __init__(self, host='localhost', port='11211'):
        self._host = host
        self._port = port

    @property
    def client(self):
        if self._client is None:
            self._client = telnetlib.Telnet(self._host, self._port)
        return self._client

    def command(self, cmd):
        """
        Writes a command to telnet and returns the response.
        """
        self.client.write("%s\n" % cmd)
        return self.client.read_until('END')

    def key_details(self, sort=True, limit=100):
        """
        Returns a list of tuples containing keys and details.
        """
        cmd = 'stats cachedump %s %s'
        keys = [key for _id in self.slab_ids() for key in self._key_regex.findall(self.command(cmd % (_id, limit)))]
        if sort:
            return sorted(keys)
        else:
            return keys

    def keys(self, sort=True, limit=100):
        """
        Returns a list of keys in use.
        """
        return [key[0] for key in self.key_details(sort=sort, limit=limit)]

    def slab_ids(self):
        """
        Returns a list of slab ids in use.
        """
        return self._slab_regex.findall(self.command('stats items'))

    def stats(self):
        """
        Returns a dict containing memcached stats.
        """
        return dict(self._stat_regex.findall(self.command('stats')))


def main(argv=None):
    if not argv:
        argv = sys.argv
    host = argv[1] if len(argv) >= 2 else '127.0.0.1'
    port = argv[2] if len(argv) >= 3 else '11211'
    import pprint
    m = MemcachedStats(host, port)
    pprint.pprint(m.keys())

if __name__ == '__main__':
    main()