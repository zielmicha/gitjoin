import fcntl
import urllib
import os
import tempfile
import functools
import marshal
import zlib

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
        split = split + ('',)
    
    type, value, author = split
    
    if type != 'ssh-rsa':
        raise ValueError('Wrong key type.')
    
    data = value.decode('base64').encode('base64').replace('\n', '')
    author = urllib.quote(author.strip())
    
    return '%s %s %s' % (type, data, author)

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

class Cache:
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

global_cache = Cache(os.path.expanduser('~/var/cache'))

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

