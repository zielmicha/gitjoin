# Gitjoin Git Management
# Copyright (C) 2012 Michal Zielinski
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import fcntl
import urllib
import os
import tempfile
import functools
import marshal
import zlib
import sys
import time
import atexit
import hashlib

class lock(object):
    ' exclusive by default '
    def __init__(self, name, shared=False):
        self.path = os.path.expanduser('~/var/locks/' + quote_path(name))
        self.shared = shared
        self.fd = open(self.path, 'w+')

    def __enter__(self):
        fcntl.lockf(self.fd, fcntl.LOCK_SH if self.shared else fcntl.LOCK_EX)

    def __exit__(self, *args):
        fcntl.lockf(self.fd, fcntl.LOCK_UN)

def global_lock(shared=True):
    ' shared by default '
    return lock('global', shared=shared)

def quote_path(s):
    return urllib.quote(s, safe='')

def get_conf(name):
    config = {}
    execfile(os.path.expanduser('~/config.py'), config)
    return config[name]

def overwrite_file(path, data, tmp_dir=os.path.expanduser('~/var/tmp/')):
    ' Atomic overwrite using os.rename (which is guaranteed to be atomic) '
    tmp_file = tempfile.NamedTemporaryFile(dir=tmp_dir, prefix='overwrite_', delete=False)
    tmp_file.write(data)
    tmp_file.close()
    os.rename(tmp_file.name, path)

def reformat_ssh_key(data):
    split = data.split(None, 2)
    if len(split) < 2:
        raise ValueError('Not enough values in SSH key.')

    if len(split) == 2:
        split = split + ['',]

    type, value, author = split

    if type != 'ssh-rsa':
        raise ValueError('Wrong key type.')

    data = value.decode('base64').encode('base64').replace('\n', '')
    author = urllib.quote(author.strip())

    return '%s %s %s' % (type, data, author)

def get_ssh_key_fingerprint(data):
    ' Assumes well-formed SSH key '
    key = data.split(None, 2)[1]
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join( a + b for a,b in zip(fp_plain[::2], fp_plain[1::2]) )

def reusable_generator(method):
    def decorator(*args, **kwargs):
        return list(method(*args, **kwargs))

    functools.update_wrapper(decorator, method)
    return decorator

def none_on_error(func, errors=None, none_value=None, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as err:
        if errors:
            if not isinstance(err, tuple(errors)):
                raise
        return None

class FSCache:
    def __init__(self, path):
        self.path = path

    def __setitem__(self, key, val):
        assert isinstance(key, str)
        cache_val = marshal.dumps(val)
        return overwrite_file(self.path + '/' + quote_path(key), zlib.compress(cache_val), tmp_dir=self.path)

    def __getitem__(self, key):
        try:
            data = open(self.path + '/' + quote_path(key)).read()
        except IOError:
            raise KeyError(key)
        else:
            return marshal.loads(zlib.decompress(data))

class KyotoCache:
    def __init__(self, path):
        self.path = path
        self.db = None

    def _open(self):
        if self.db:
            return
        self.db = kyotocabinet.DB()
        # it's important to close db softly or next time it will recover for ~30s/1GB
        atexit.register(lambda: self.close())
        if not self.db.open(self.path, kyotocabinet.DB.OWRITER | kyotocabinet.DB.OCREATE):
            raise IOError('Failed to open %s' % path)

    def __setitem__(self, key, val):
        self._open()
        assert isinstance(key, str)
        cache_val = zlib.compress(marshal.dumps(val))
        self.db.set(key, cache_val)

    def __getitem__(self, key):
        self._open()
        data = self.db.get(key)
        if not data:
            raise KeyError(key)
        else:
            return marshal.loads(zlib.decompress(data))

    def __del__(self):
        self.close()

    def close(self):
        if self.db:
            self.db.close()

global_cache = FSCache(os.path.expanduser('~/var/cache'))

def cached(key, cache=global_cache, funcid=None):
    def dec_apply(func):
        key_prefix = quote_path(funcid or func.__module__ + '.' + func.__name__)
        def decorator(*args, **kwargs):
            ret_key = key(*args, **kwargs)
            if isinstance(ret_key, tuple):
                ret_key = ','.join( quote_path(str(part)) for part in ret_key )
            elif not isinstance(ret_key, str):
                raise TypeError('key() function returned unsupported key type %r' % ret_key)
            cache_key = key_prefix + ',' + ret_key
            try:
                val = cache[cache_key]
                return val
            except KeyError:
                val = func(*args, **kwargs)
                cache[cache_key] = val
                return val

        functools.update_wrapper(decorator, func)
        return decorator

    return dec_apply

def split_path(path):
    fragments = path.split('/')
    return [ ('/'.join(fragments[:i]), fragments[i]) for i in xrange(len(fragments)) ]

if __name__ == '__main__':
    cache_path = tempfile.mkdtemp()
    print 'using cache at', cache_path
    cache = Cache(cache_path)

    @cached(key=lambda c: (c, ), cache=cache)
    def expensive_comp(c):
        print 'computing 2*%r' % c
        return 2*c

    print expensive_comp(2)
    print expensive_comp(2)
    print expensive_comp(2.5)
    print expensive_comp(2.0)
    print expensive_comp('../../ble')
    print expensive_comp('../../ble')
    print expensive_comp(3)
