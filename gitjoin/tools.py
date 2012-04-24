import fcntl
import urllib
import os
import tempfile

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

def get_conf(name):
    config = {}
    execfile(os.path.expanduser('~/config.py'), config)
    return config[name]

def overwrite_file(path, data):
    ' Atomic overwrite using os.rename (which is guaranted to be atomic) '
    tmp_dir = os.path.expanduser('~/var/tmp/')
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