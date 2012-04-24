import fcntl
import urllib
import os

class lock(object):
    ' exclusive by default '
    def __init__(self, name, shared=False):
        self.path = os.path.expanduser('~/var/locks/' + urllib.quote(name, safe=''))
        self.shared = shared
        self.fd = open(self.path, 'w+')
    
    def __enter__(self):
        fcntl.lockf(self.fd, fcntl.LOCK_SH if self.shared else fcntl.LOCK_EX)
    
    def __exit__(self, *args):
        fcntl.lockf(self.fd, fcntl.LOCK_UN)

def global_lock(shared=True):
    ' shared by default '
    return lock('global', shared=shared)