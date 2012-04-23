#!/usr/bin/env python
import httplib
import sys
import os
import shlex
import subprocess

import tools

def main():
    username, = sys.argv[1:]
    command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    cmd, _, arg = command.partition(' ')
    
    if cmd in ('git-upload-pack', 'git-receive-pack'):
        args_split = shlex.split(arg)
        if len(args_split) != 1:
            sys.exit('Unexpected number of arguments: %s' % len(args_split))
        repo = args_split[0]
        invoke_command(cmd, repo)
    else:
        sys.exit('Expected git-upload-pack or git-receive-pack, got %s instead.' % (cmd or 'nothing'))

def invoke_command(cmd, repo):
    try:
        path = get_path(cmd, repo)
    except PermissionDenied as err:
        sys.exit('Cannot access repository %s: %s' % (repo, err.message))
    
    with tools.lock('repo_' + path):
        status = subprocess.call((cmd, path))
    
    sys.exit(status)

def get_path(cmd, repo):
    if repo == 'i-dont-like-you':
        raise PermissionDenied('I don\'t like you.')
    else:
        return os.path.expanduser('~/repos/' + repo)

class PermissionDenied(Exception): pass

if __name__ == '__main__':
    main()
