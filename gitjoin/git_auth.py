#!/usr/bin/env python
import httplib
import sys
import os
import shlex
import subprocess
import urllib

import tools

def main():
    auth_obj, = sys.argv[1:]
    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    cmd, _, arg = command.partition(' ')
    
    if cmd in ('git-upload-pack', 'git-receive-pack'):
        args_split = shlex.split(arg)
        if len(args_split) != 1:
            sys.exit('Unexpected number of arguments: %s' % len(args_split))
        repo = args_split[0]
        invoke_command(auth_obj, cmd, repo)
    else:
        sys.exit('Expected git-upload-pack or git-receive-pack, got %s instead.' % (cmd or 'nothing'))

def invoke_command(auth_obj, cmd, repo):
    try:
        path = get_path(auth_obj, cmd, repo)
    except PermissionDenied as err:
        sys.exit('Cannot access repository %s: %s' % (repo, err.message))
    
    with tools.global_lock(), tools.lock('repo_' + path, shared=cmd == 'git-upload-pack'):
        if not os.path.exists(path + '/HEAD'):
            git_init(path)
        
        status = subprocess.call((cmd, path))
    
    sys.exit(status)

def get_path(auth_obj, cmd, repo):
    access = {'git-upload-pack': 'ro', 'git-receive-pack': 'rw'}[cmd]
    result = urllib.urlopen(tools.get_conf('URL').rstrip('/') + '/gitauth?' + urllib.urlencode(dict(repo=repo, auth=auth_obj, access=access))).read()
    status, msg = result.split(':', 1)
    msg = msg.strip()
    if status == 'ok':
        ident = int(msg)
        return os.path.expanduser('~/repos/%d' % ident)
    else:
        raise PermissionDenied(msg)

def git_init(path):
    if not os.path.exists(path):
        os.mkdir(path)
    os.chdir(path)
    print >>sys.stderr, 'Initializing new Git repository...'
    status = subprocess.call(('git', 'init', '--bare'), stdout=sys.stderr)
    if status != 0:
        sys.exit('Initialization failed.')

class PermissionDenied(Exception): pass

if __name__ == '__main__':
    main()
